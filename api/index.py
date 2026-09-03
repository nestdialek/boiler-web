import math
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# HTML-шаблон страницы калькулятора
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Boiler Circulation Calculator</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }
        .container { max-width: 600px; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 0 auto; }
        h2 { color: #333; text-align: center; margin-bottom: 20px; }
        h3 { border-bottom: 2px solid #ddd; padding-bottom: 5px; color: #444; margin-top: 20px; }
        .form-group { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        label { font-size: 14px; color: #555; width: 60%; }
        input, select { padding: 8px; width: 35%; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 20px; }
        button:hover { background: #0056b3; }
        .results { margin-top: 25px; padding: 15px; border-radius: 6px; background: #e9ecef; }
        .verdict { font-weight: bold; margin-top: 10px; white-space: pre-wrap; padding: 10px; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; }
        .danger { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
<div class="container">
    <h2>Boiler Circulation Calculator</h2>
    <form method="post">
        <div class="form-group">
            <label>Unit System:</label>
            <select name="sys">
                <option value="Imperial" {imp_sel}>Imperial (psi, in, ft, lb/h)</option>
                <option value="Metric" {met_sel}>Metric (MPa, mm, m, kg/s)</option>
            </select>
        </div>
        
        <h3>1. Operating Mode</h3>
        <div class="form-group"><label>Drum Pressure:</label><input type="number" step="any" name="raw_P" value="{raw_P}" required></div>
        <div class="form-group"><label>Loop Height:</label><input type="number" step="any" name="raw_H" value="{raw_H}" required></div>
        <div class="form-group"><label>Steam Capacity:</label><input type="number" step="any" name="raw_Q" value="{raw_Q}" required></div>
        
        <h3>2. Feeders Configuration</h3>
        <div class="form-group"><label>Number of Feeders (pcs):</label><input type="number" name="N_down" value="{N_down}" required></div>
        <div class="form-group"><label>Internal Diameter:</label><input type="number" step="any" name="raw_D_down" value="{raw_D_down}" required></div>
        <div class="form-group"><label>Total Pipe Length:</label><input type="number" step="any" name="raw_L_down" value="{raw_L_down}" required></div>
        <div class="form-group"><label>Resistance Coeff. (Zeta):</label><input type="number" step="any" name="Zeta_down" value="{Zeta_down}" required></div>
        
        <h3>3. Risers Configuration</h3>
        <div class="form-group"><label>Number of Risers (pcs):</label><input type="number" name="N_rise" value="{N_rise}" required></div>
        <div class="form-group"><label>Internal Diameter:</label><input type="number" step="any" name="raw_D_rise" value="{raw_D_rise}" required></div>
        <div class="form-group"><label>Total Pipe Length:</label><input type="number" step="any" name="raw_L_rise" value="{raw_L_rise}" required></div>
        <div class="form-group"><label>Resistance Coeff. (Zeta):</label><input type="number" step="any" name="Zeta_rise" value="{Zeta_rise}" required></div>
        
        <button type="submit">CALCULATE</button>
    </form>

    {result_block}
</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    # Отображение пустой формы по умолчанию при первом входе на сайт
    return HTML_TEMPLATE.format(
        imp_sel="selected", met_sel="", raw_P=0, raw_H=0, raw_Q=0,
        N_down=0, raw_D_down=0, raw_L_down=0, Zeta_down=0,
        N_rise=0, raw_D_rise=0, raw_L_rise=0, Zeta_rise=0,
        result_block=""
    )

@app.post("/", response_class=HTMLResponse)
async def calculate(
    sys: str = Form(...), raw_P: float = Form(...), raw_H: float = Form(...), raw_Q: float = Form(...),
    N_down: int = Form(...), raw_D_down: float = Form(...), raw_L_down: float = Form(...), Zeta_down: float = Form(...),
    N_rise: int = Form(...), raw_D_rise: float = Form(...), raw_L_rise: float = Form(...), Zeta_rise: float = Form(...),
):
    try:
        # Конвертация единиц в СИ для ядра гидравлического расчета
        if sys == "Metric":
            P_MPa, H_m, Q_kg_s = raw_P, raw_H, raw_Q
            D_down_m, L_down_m = raw_D_down / 1000.0, raw_L_down
            D_rise_m, L_rise_m = raw_D_rise / 1000.0, raw_L_rise
            v_unit = "m/s"
        else:
            P_MPa = raw_P * 0.00689476
            H_m = raw_H * 0.3048
            Q_kg_s = raw_Q * 0.000125998
            D_down_m = raw_D_down * 0.0254
            L_down_m = raw_L_down * 0.3048
            D_rise_m = raw_D_rise * 0.0254
            L_rise_m = raw_L_rise * 0.3048
            v_unit = "ft/s"

        if P_MPa < 0.1 or P_MPa > 16:
            raise ValueError("Pressure out of stable limits (0.1 - 16 MPa / 14.5 - 2320 psi).")

        rho_w = 1000.0 - 55.0 * P_MPa
        rho_s = 5.0 * P_MPa
        viscosity, k_rough = 1.1e-4, 0.00015

        F_down = N_down * (math.pi * D_down_m**2 / 4)
        F_rise = N_rise * (math.pi * D_rise_m**2 / 4)

        v_down, step, balance_found = 0.01, 0.001, False

        while v_down < 10.0:
            G_circ = rho_w * v_down * F_down
            if G_circ <= Q_kg_s:
                v_down += step
                continue
            K = G_circ / Q_kg_s
            x_avg = 0.5 / K
            rho_mix = 1 / ((x_avg / rho_s) + ((1 - x_avg) / rho_w))
            S_dv = 9.81 * H_m * (rho_w - rho_mix)

            lambda_down = 0.11 * (k_rough/D_down_m + 68/(rho_w * v_down * D_down_m / viscosity))**0.25
            v_rise = G_circ / (rho_mix * F_rise)
            lambda_rise = 0.11 * (k_rough/D_rise_m + 68/(0.01 if rho_mix <= 0 else (rho_mix * v_rise * D_rise_m / viscosity)))**0.25

            dP_down = (lambda_down * L_down_m / D_down_m + Zeta_down) * (rho_w * v_down**2 / 2)
            dP_rise = (lambda_rise * L_rise_m / D_rise_m + Zeta_rise) * (rho_mix * v_rise**2 / 2)

            if (dP_down + dP_rise) >= S_dv:
                balance_found = True
                break
            v_down += step

        if not balance_found:
            raise Exception("Hydraulic resistance is too high. Circulation is blocked!")

        display_v = v_down if sys == "Metric" else v_down / 0.3048

        # Формирование вердикта о надежности контура
        verdict = ""
        if v_down > 2.5:
            v_lim = "2.5 m/s" if sys == "Metric" else "8.2 ft/s"
            verdict += f"⚠️ Warning! Velocity in feeders is too HIGH (> {v_lim}). Consider increasing diameter.\\n"
        elif v_down < 0.4:
            v_lim = "0.4 m/s" if sys == "Metric" else "1.3 ft/s"
            verdict += f"⚠️ Warning! Flow velocity is too low (< {v_lim}). Risk of flow stagnation.\\n"
            
        if K < 10.0:
            verdict += "❌ CRITICALLY LOW CIRCULATION RATIO (K < 10)! Urgently increase diameters to prevent burnout.\\n"

        if verdict == "":
            verdict = "✅ Hydraulic loop is completely stable! Diameters are safe."
            v_class = "success"
        else:
            v_class = "danger"

        result_block = f"""
        <div class="results">
            <strong>Velocity in feeders:</strong> {display_v:.2f} {v_unit}<br>
            <strong>Circulation ratio (K):</strong> {K:.1f}<br>
            <div class="verdict {v_class}">{verdict}</div>
        </div>
        """
    except Exception as e:
        result_block = f'<div class="results"><div class="verdict danger">❌ Error: {str(e)}</div></div>'

    # Передача значений обратно в поля, чтобы они не стирались после отправки формы
    return HTML_TEMPLATE.format(
        imp_sel="selected" if sys == "Imperial" else "",
        met_sel="selected" if sys == "Metric" else "",
        raw_P=raw_P, raw_H=raw_H, raw_Q=raw_Q,
        N_down=N_down, raw_D_down=raw_D_down, raw_L_down=raw_L_down, Zeta_down=Zeta_down,
        N_rise=N_rise, raw_D_rise=raw_D_rise, raw_L_rise=raw_L_rise, Zeta_rise=Zeta_rise,
        result_block=result_block
    )

# Обязательная точка интеграции с Serverless-платформой Vercel
app = app
