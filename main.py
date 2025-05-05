from flask import Flask, request
import psycopg2
from datetime import datetime, timedelta
import calendar
import locale

#locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Nombres en español en sistemas compatibles
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')

app = Flask(__name__)

DB_CONFIG = {
    "host": "3.146.81.42",
    "port": 5432,
    "dbname": "db_theblancgroup5",
    "user": "odoo",
    "password": "tbg1414"
}

def fetch_data(query, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query, params or ())
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.route('/')
def dashboard():
    now = datetime.now()
    mes_actual = int(request.args.get('mes', now.month))
    semana_actual = int(request.args.get('semana', now.isocalendar()[1]))
    anio_actual = int(request.args.get('anio', now.year))
    from babel.dates import format_date
    nombre_mes = format_date(now, "LLLL", locale='es')

    fecha_actual = now.strftime(f"%Y - {nombre_mes} - %d")

    dias_hasta_sabado = (5 - now.weekday()) % 7
    proximo_sabado = (now + timedelta(days=dias_hasta_sabado)).replace(hour=0, minute=0, second=0, microsecond=0)
    segundos_restantes = int((proximo_sabado - now).total_seconds())

    options_mes = ''.join([f'<option value="{i}" {"selected" if i == mes_actual else ""}>{calendar.month_name[i].capitalize()}</option>' for i in range(1, 13)])
    options_semana = ''.join([f'<option value="{i}" {"selected" if i == semana_actual else ""}>{i}</option>' for i in range(1, 54)])
    options_anio = ''.join([f'<option value="{y}" {"selected" if y == anio_actual else ""}>{y}</option>' for y in range(now.year - 5, now.year + 1)])

    def build_label_with_priorities(periodo_value, periodo_expr):
        query = f"""
            SELECT COALESCE(p.name, 'Sin asignar') AS usuario,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE l.x_priority IS NULL OR l.x_priority = '0') AS sin,
                   COUNT(*) FILTER (WHERE l.x_priority = '1') AS bajas,
                   COUNT(*) FILTER (WHERE l.x_priority = '2') AS medias,
                   COUNT(*) FILTER (WHERE l.x_priority = '3') AS altas
            FROM crm_lead l
            LEFT JOIN res_users u ON u.id = l.user_id
            LEFT JOIN res_partner p ON p.id = u.partner_id
            WHERE l.active = TRUE AND {periodo_expr} = %s
            GROUP BY usuario
        """
        rows = fetch_data(query, (periodo_value,))
        labels = [
            f"{r[0]} ({r[1]}) ({r[2]}s + {r[3]}L + {r[4]}M + {r[5]}H)"
            for r in rows
        ]
        values = [r[1] for r in rows]
        return labels, values

    labels_mensual, values_mensual = build_label_with_priorities(mes_actual, "DATE_PART('month', l.create_date)")
    labels_semanal, values_semanal = build_label_with_priorities(semana_actual, "DATE_PART('week', l.create_date)")
    labels_anual, values_anual = build_label_with_priorities(anio_actual, "DATE_PART('year', l.create_date)")

    import json
    return f"""
    <!DOCTYPE html>
    <html lang='es'>
    <head>
        <meta charset='UTF-8'>
        <title>DASHBOARD FOR</title>
        <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
        <script src='https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2'></script>
        <style>
            body {{ background-color: #111; color: white; font-family: Arial; text-align: center; }}
            .chart-row {{ display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }}
            .chart-container {{ width: 30%; padding: 20px; background-color: #222; border-radius: 10px; }}
            .header-info {{ margin: 20px; }}
            img.logo {{ width: 120px; margin-top: 10px; }}
            #cuenta {{ font-size: 5em; color: red; font-family: 'Courier New', monospace; }}
        </style>
    </head>
    <body>
        <img class='logo' src='https://forhumancapital.mx/wp-content/uploads/2025/01/FORLOGOTRANSPARENTwhite.png' alt='Logo FOR'>
        <h1>DASHBOARD FOR</h1>
        <div class='header-info'>
            <p><strong>{fecha_actual}</strong></p>
            <p><span id='cuenta'>00:00:00</span></p>
        </div>

        <div class='chart-row'>
            <div id='leadsContainer' style='margin-top:40px; text-align:left; padding:20px;'></div>
            <div class='chart-container'>
                <h2>Leads Activos por Usuario ({anio_actual})
                    <select onchange="location.href='/?mes={mes_actual}&semana={semana_actual}&anio=' + this.value">
                        {options_anio}
                    </select>
                </h2>
                <canvas id='chartAnual'></canvas>
            </div>

            <div class='chart-container'>
                <h2>Leads Activos por Usuario ({nombre_mes})
                    <select id='selectMes' onchange="location.href='/?mes=' + this.value + '&semana={semana_actual}&anio={anio_actual}'">
                        {options_mes}
                    </select>
                </h2>
                <canvas id='chartMes'></canvas>
            </div>

            <div class='chart-container'>
                <h2>Leads Activos por Usuario (Semana {semana_actual})
                    <select id='selectSemana' onchange="location.href='/?mes={mes_actual}&semana=' + this.value + '&anio={anio_actual}'">
                        {options_semana}
                    </select>
                </h2>
                <canvas id='chartSemana'></canvas>
            </div>
        </div>

        <script>
            const chartOptions = {{
                plugins: {{
                    legend: {{ labels: {{ color: 'white' }} }},
                    datalabels: {{
                        color: 'white',
                        font: {{ weight: 'bold' }},
                        formatter: (value, context) => context.chart.data.labels[context.dataIndex],
                        align: 'center',
                        anchor: 'center'
                    }}
                }}
            }};

            Chart.register(ChartDataLabels);

            const chartAnual = new Chart(document.getElementById('chartAnual').getContext('2d'), {{
                type: 'pie',
                data: {{ labels: {json.dumps(labels_anual)}, datasets: [{{ data: {json.dumps(values_anual)}, backgroundColor: ['#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56', '#9966FF', '#FF9F40'], borderColor: 'black', borderWidth: 1 }}] }},
                options: chartOptions
            }});

            new Chart(document.getElementById('chartMes').getContext('2d'), {{
                type: 'pie',
                data: {{ labels: {json.dumps(labels_mensual)}, datasets: [{{ data: {json.dumps(values_mensual)}, backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'], borderColor: 'black', borderWidth: 1 }}] }},
                options: chartOptions
            }});

            new Chart(document.getElementById('chartSemana').getContext('2d'), {{
                type: 'doughnut',
                data: {{ labels: {json.dumps(labels_semanal)}, datasets: [{{ data: {json.dumps(values_semanal)}, backgroundColor: ['#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56', '#9966FF', '#FF9F40'], borderColor: 'black', borderWidth: 1 }}] }},
                options: chartOptions
            }});

            document.getElementById('chartAnual').onclick = function(evt) {{
                const points = chartAnual.getElementsAtEventForMode(evt, 'nearest', {{ intersect: true }}, true);
                if (points.length) {{
                    const index = points[0].index;
                    const label = chartAnual.data.labels[index].split(' (')[0];
                    fetch('/leads?user=' + encodeURIComponent(label))
                        .then(response => response.text())
                        .then(html => {{
                            document.getElementById('leadsContainer').innerHTML = "<h3>Leads de " + label + "</h3>" + html;
                        }});
                }}
            }};

            let segundos = {segundos_restantes};
            const cuenta = document.getElementById('cuenta');
            setInterval(() => {{
                if (segundos > 0) {{
                    let hrs = String(Math.floor(segundos / 3600)).padStart(2, '0');
                    let mins = String(Math.floor((segundos % 3600) / 60)).padStart(2, '0');
                    let secs = String(segundos % 60).padStart(2, '0');
                    cuenta.innerText = `${{hrs}}:${{mins}}:${{secs}}`;
                    segundos--;
                }} else {{ cuenta.innerText = "00:00:00"; }}
            }}, 1000);
        </script>
    </body>
    </html>
    """

@app.route('/leads')
def get_leads():
    user = request.args.get('user')
    query = """
        SELECT l.name, l.contact_name, l.email_from
        FROM crm_lead l
        LEFT JOIN res_users u ON u.id = l.user_id
        LEFT JOIN res_partner p ON p.id = u.partner_id
        WHERE COALESCE(p.name, 'Sin asignar') = %s AND l.active = TRUE
    """
    rows = fetch_data(query, (user,))
    html = "<ul>"
    for name, contact, email in rows:
        html += f"<li><strong>{name}</strong> — {contact or 'Sin contacto'} — {email or 'Sin email'}</li>"
    html += "</ul>" if rows else "<p>No hay leads disponibles.</p>"
    return html

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
