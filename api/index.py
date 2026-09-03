# @title
import math

def calculate_circulation():
    print("=== UNIVERSAL BOILER CIRCULATION CALCULATOR ===")
    print("Select unit system:")
    print("1 - Metric (MPa, mm, meters, kg/s)")
    print("2 - Imperial (psi, inches, feet, lb/h)")

    choice = input("Enter 1 or 2: ").strip()
    sys = "Metric" if choice == "1" else "Imperial"

    print(f"\nSelected system: {'Metric' if sys == 'Metric' else 'Imperial'}\n")

    try:
        # 1. DATA INPUT
        if sys == "Metric":
            raw_P = float(input("Drum pressure (MPa) [e.g., 4.0]: ").replace(',', '.'))
            raw_H = float(input("Circulation loop height (meters) [e.g., 12.0]: ").replace(',', '.'))
            raw_Q = float(input("Loop steam capacity (kg/s) [e.g., 2.5]: ").replace(',', '.'))

            N_down = int(input("Number of feeders (pcs) [e.g., 4]: "))
            raw_D_down = float(input("Feeders internal diameter (mm) [6\" ~ 150]: ").replace(',', '.'))
            raw_L_down = float(input("Single feeder pipe length (meters) [e.g., 15.0]: ").replace(',', '.'))
            Zeta_down = float(input("Feeders local resistance coefficient (Zeta) [e.g., 2.5]: ").replace(',', '.'))

            N_rise = int(input("Number of risers (pcs) [e.g., 5]: "))
            raw_D_rise = float(input("Risers internal diameter (mm) [8\" ~ 200]: ").replace(',', '.'))
            raw_L_rise = float(input("Single riser pipe length (meters) [e.g., 14.0]: ").replace(',', '.'))
            Zeta_rise = float(input("Risers local resistance coefficient (Zeta) [e.g., 2.0]: ").replace(',', '.'))

            # Convert to SI
            P_MPa = raw_P
            H_m = raw_H
            Q_kg_s = raw_Q
            D_down_m = raw_D_down / 1000.0
            L_down_m = raw_L_down
            D_rise_m = raw_D_rise / 1000.0
            L_rise_m = raw_L_rise
        else:
            raw_P = float(input("Drum pressure (psi) [e.g., 580]: ").replace(',', '.'))
            raw_H = float(input("Circulation loop height (feet) [e.g., 20.0]: ").replace(',', '.'))
            raw_Q = float(input("Loop steam capacity (lb/h) [e.g., 20000]: ").replace(',', '.'))

            N_down = int(input("Number of feeders (pcs) [e.g., 4]: "))
            raw_D_down = float(input("Feeders internal diameter (inches) [e.g., 6]: ").replace(',', '.'))
            raw_L_down = float(input("Single feeder pipe length (feet) [e.g., 45.0]: ").replace(',', '.'))
            Zeta_down = float(input("Feeders local resistance coefficient (Zeta) [e.g., 2.5]: ").replace(',', '.'))

            N_rise = int(input("Number of risers (pcs) [e.g., 5]: "))
            raw_D_rise = float(input("Risers internal diameter (inches) [e.g., 8]: ").replace(',', '.'))
            raw_L_rise = float(input("Single riser pipe length (feet) [e.g., 42.0]: ").replace(',', '.'))
            Zeta_rise = float(input("Risers local resistance coefficient (Zeta) [e.g., 2.0]: ").replace(',', '.'))

            # Convert Imperial to SI
            P_MPa = raw_P * 0.00689476             # psi to MPa
            H_m = raw_H * 0.3048                    # ft to m
            Q_kg_s = raw_Q * 0.000125998            # lb/h to kg/s
            D_down_m = raw_D_down * 0.0254          # inches to m
            L_down_m = raw_L_down * 0.3048          # feet to m
            D_rise_m = raw_D_rise * 0.0254          # inches to m
            L_rise_m = raw_L_rise * 0.3048          # feet to m

        # 2. PRESSURE LIMIT CHECK
        if P_MPa < 0.1 or P_MPa > 16:
            print("\n❌ Error: Pressure is out of stable engineering algorithm limits (0.1 - 16 MPa / 14.5 - 2320 psi).")
            return

        # Fluid physical properties approximation
        rho_w = 1000.0 - 55.0 * P_MPa
        rho_s = 5.0 * P_MPa
        viscosity = 1.1e-4
        k_rough = 0.00015

        F_down = N_down * (math.pi * D_down_m**2 / 4)
        F_rise = N_rise * (math.pi * D_rise_m**2 / 4)

        v_down = 0.01
        step = 0.001
        balance_found = False

        # 3. ITERATIVE CYCLE FOR BALANCE SEARCH
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

            if rho_mix <= 0 or v_rise <= 0:
                lambda_rise = 0.02
            else:
                lambda_rise = 0.11 * (k_rough/D_rise_m + 68/(rho_mix * v_rise * D_rise_m / viscosity))**0.25

            dP_down = (lambda_down * L_down_m / D_down_m + Zeta_down) * (rho_w * v_down**2 / 2)
            dP_rise = (lambda_rise * L_rise_m / D_rise_m + Zeta_rise) * (rho_mix * v_rise**2 / 2)

            if (dP_down + dP_rise) >= S_dv:
                balance_found = True
                break
            v_down += step

        if not balance_found:
            print("\n❌ Calculation Error: Hydraulic resistance is too high. Circulation is blocked!")
            return

        # Convert back to selected output units
        if sys == "Metric":
            display_v = v_down
            v_unit = "m/s"
        else:
            display_v = v_down / 0.3048
            v_unit = "ft/s"

        # 4. OUTPUT RESULTS
        print("\n" + "="*40)
        print(" CALCULATION RESULTS:")
        print("="*40)
        print(f"Velocity in feeders:                {display_v:.2f} {v_unit}")
        print(f"Loop circulation ratio (K):         {K:.1f}")
        print("-"*40)
        print("RELIABILITY ANALYSIS & VERDICT:")
        print("-"*40)

        verdict = ""
        if v_down > 2.5:
            v_lim = "2.5 m/s" if sys == "Metric" else "8.2 ft/s"
            verdict += f"⚠️ Warning! Velocity in feeders is too HIGH (> {v_lim}).\nRECOMMENDATION: INCREASE THE DIAMETER or quantity of feeders to reduce head losses.\n\n"
        elif v_down < 0.4:
            v_lim = "0.4 m/s" if sys == "Metric" else "1.3 ft/s"
            verdict += f"⚠️ Flow velocity is too low (< {v_lim}). Risk of flow stagnation or circulation reversal.\n\n"

        if K < 10.0:
            verdict += "❌ CRITICALLY LOW CIRCULATION RATIO (K < 10)!\nWater evaporates too fast. Risers are at risk of burnout due to boiling crisis.\nRECOMMENDATION: Urgently INCREASE THE DIAMETER of feeders OR risers to improve flow rate.\n\n"

        if dP_down > (dP_down + dP_rise) * 0.65:
            verdict += "💡 Engineering note: Feeders friction resistance dominates the system. Avoid adding extra bends/elbows when moving nozzles.\n\n"

        if verdict == "":
            print("✅ Hydraulic loop is completely stable!")
            print("Flow velocities are safe, and the circulation ratio is within norms. Pipe diameter changes are not required.")
        else:
            print(verdict.strip())
        print("="*40)

    except ValueError:
        print("\n❌ Error: Please enter numeric values only. Use a dot as a decimal separator (e.g., 15.5).")

if __name__ == "__main__":
    calculate_circulation()

# Обязательная точка интеграции с Serverless-платформой Vercel
app = app
