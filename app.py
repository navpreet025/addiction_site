from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime

app = Flask(__name__)

# ---- paths & folders ----
DATASET_PATH = "addiction_population_data.csv"
CHARTS_DIR = os.path.join("static", "charts")
FORM_DIR = "data"
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(FORM_DIR, exist_ok=True)

# ---- load data once ----
df = pd.read_csv(DATASET_PATH)

def generate_charts():
    """Save simple charts into static/charts/"""
    # Drinks per week (top 10 countries)
    if {"country", "drinks_per_week"}.issubset(df.columns):
        drinks = (
            df.groupby("country")["drinks_per_week"]
              .mean().sort_values(ascending=False).head(10)
        )
        plt.figure(figsize=(9,5))
        drinks.plot(kind="bar")
        plt.title("Average Drinks per Week by Country (Top 10)")
        plt.ylabel("Drinks per Week")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(os.path.join(CHARTS_DIR, "drinks_chart.png"))
        plt.close()

    # Smokes per day (by gender)
    if {"gender", "smokes_per_day"}.issubset(df.columns):
        smokes = df.groupby("gender")["smokes_per_day"].mean()
        plt.figure(figsize=(6,4))
        smokes.plot(kind="bar")
        plt.title("Average Smokes per Day by Gender")
        plt.ylabel("Smokes per Day")
        plt.tight_layout()
        plt.savefig(os.path.join(CHARTS_DIR, "smokes_chart.png"))
        plt.close()

def summary():
    """Small JSON summary used on the site"""
    out = {}
    if {"country", "drinks_per_week"}.issubset(df.columns):
        out["top_countries_by_drinks"] = (
            df.groupby("country")["drinks_per_week"].mean()
              .sort_values(ascending=False).head(5).round(2).to_dict()
        )
    if {"gender", "smokes_per_day"}.issubset(df.columns):
        out["avg_smokes_by_gender"] = (
            df.groupby("gender")["smokes_per_day"].mean()
              .round(2).to_dict()
        )
    return out

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/charts")
def charts():
    generate_charts()
    return render_template("charts.html")

@app.route("/api/summary")
def api_summary():
    return jsonify(summary())

@app.route("/contact", methods=["GET", "POST"])
def contact():
    msg = None
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        message = request.form.get("message","").strip()
        if name and email and message:
            row = f'{datetime.utcnow().isoformat()},{name},{email},"{message.replace(",", ";")}"\n'
            with open(os.path.join(FORM_DIR, "messages.csv"), "a", encoding="utf-8") as f:
                # header if file newly created
                if f.tell() == 0:
                    f.write("timestamp,name,email,message\n")
                f.write(row)
            msg = "Thanks! Your message was sent."
        else:
            msg = "Please fill in all fields."
    return render_template("contact.html", message=msg)
@app.route("/resources")
def resources():
    return render_template("resources.html")


@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if request.method == "POST":
        # Collect answers
        alcohol = request.form.get("alcohol_frequency")
        withdrawal = request.form.get("withdrawal_symptoms")
        cigarettes = request.form.get("cigarettes_per_day")
        stress = request.form.get("stress_level")
        sleep = request.form.get("sleep_trouble")
        support = request.form.get("social_support")

        data = {
            "Alcohol Frequency": alcohol,
            "Withdrawal Symptoms": withdrawal,
            "Cigarettes Per Day": cigarettes,
            "Stress Level": stress,
            "Sleep Trouble": sleep,
            "Social Support": support
        }

        # Simple scoring system
        score = 0

        # Alcohol
        if alcohol == "Daily":
            score += 3
        elif alcohol == "Weekly":
            score += 2
        elif alcohol == "Occasionally":
            score += 1

        # Withdrawal symptoms
        if withdrawal == "Yes":
            score += 2

        # Cigarettes
        if cigarettes == "6-10":
            score += 2
        elif cigarettes == "More than 10":
            score += 3
        elif cigarettes == "1-5":
            score += 1

        # Stress level
        if stress == "High":
            score += 2
        elif stress == "Moderate":
            score += 1

        # Sleep trouble
        if sleep == "Yes":
            score += 1

        # Social support
        if support == "No Support":
            score += 2
        elif support == "Some Support":
            score += 1

        # Determine risk level
        if score <= 3:
            risk = "Low Risk"
            message = "Great! You seem to have healthy habits, keep maintaining them."
        elif 4 <= score <= 7:
            risk = "Moderate Risk"
            message = "You may want to monitor your habits and seek support if needed."
        else:
            risk = "High Risk"
            message = "It looks like you may be at risk. Please consider reaching out for professional help."

        return render_template("assessment_result.html", data=data, risk=risk, message=message)

    return render_template("assessment.html")

@app.route("/streak")
def streak():
    return render_template("streak.html")


if __name__ == "__main__":
    # build charts once on start
    generate_charts()
    app.run(debug=True)
