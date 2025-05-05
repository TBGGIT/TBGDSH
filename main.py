from flask import Flask, render_template_string
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "3.146.81.42",
    "port": 5432,
    "dbname": "db_theblancgroup5",
    "user": "odoo",
    "password": "tbg1414"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Leads Activos</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 13px; }
        th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .total { font-weight: bold; }
    </style>
</head>
<body>
    <h1>Total de Leads Activos: {{ total }}</h1>
    <table>
        <tr>
            <th>Oportunidad</th>
            <th>Empresa</th>
            <th>Contacto</th>
            <th>Giro</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Estado</th>
            <th>Asociado</th>
            <th>Generador</th>
            <th>Inductor</th>
            <th>Cerrador</th>
            <th>Línea de Negocio</th>
            <th>Alta</th>
            <th>Últ. Etapa</th>
            <th>Fuente</th>
            <th>Ingreso Esperado</th>
            <th>Etapa</th>
            <th>Prioridad</th>
        </tr>
        {% for row in leads %}
        <tr>
            {% for item in row %}
            <td>{{ item }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/')
def leads_activos():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT
                name,
                partner_name,
                contact_name,
                x_giro_empresa,
                email_from,
                phone,
                state_id,
                user_id,
                x_user_seg,
                x_inductor,
                x_cerrador,
                x_giros,
                create_date,
                date_last_stage_update,
                x_fuentecontacto,
                expected_revenue,
                stage_id,
                x_priority
            FROM crm_lead
            WHERE active = TRUE
            ORDER BY create_date DESC
        """)
        leads = cur.fetchall()
        total = len(leads)
        cur.close()
        conn.close()
        return render_template_string(HTML_TEMPLATE, total=total, leads=leads)
    except Exception as e:
        return f"<h1>Error al conectar o consultar: {e}</h1>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
