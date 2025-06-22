import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import base64
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

def generate_eda_report(data_store, file_id, action_history):
    data = data_store[file_id]
    df = data["current_df"]
    file_name = data.get("filename", "dataset.csv")
    actions = data.get("actions", [])
    
    # Create report directory
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/report_{file_id}.pdf"
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Exploratory Data Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # Add metadata
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"File: {file_name}", ln=True)
    pdf.cell(200, 10, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 10, txt=f"Rows: {df.shape[0]}, Columns: {df.shape[1]}", ln=True)
    pdf.ln(15)
    
    # Section 1: Data Overview
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="1. Data Overview", ln=True)
    pdf.set_font("Arial", size=10)
    
    # Basic stats
    missing_values = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    pdf.cell(200, 6, txt=f"• Missing Values: {missing_values}", ln=True)
    pdf.cell(200, 6, txt=f"• Duplicate Rows: {duplicate_rows}", ln=True)
    pdf.cell(200, 6, txt=f"• Numeric Columns: {', '.join(numeric_cols)}", ln=True)
    pdf.cell(200, 6, txt=f"• Categorical Columns: {', '.join(categorical_cols)}", ln=True)
    pdf.ln(10)
    
    # Data sample
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Data Sample (first 5 rows):", ln=True)
    pdf.set_font("Arial", size=8)
    
    # Create table header
    cols = df.columns.tolist()
    col_width = 190 / len(cols)
    for col in cols:
        pdf.cell(col_width, 6, txt=str(col), border=1)
    pdf.ln()
    
    # Add table rows
    for i, row in df.head(5).iterrows():
        for col in cols:
            pdf.cell(col_width, 6, txt=str(row[col]), border=1)
        pdf.ln()
    pdf.ln(15)
    
    # Section 2: Processing History
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="2. Processing Steps", ln=True)
    pdf.set_font("Arial", size=10)
    
    if actions:
        for action in actions:
            pdf.cell(200, 6, txt=f"• {action}", ln=True)
    else:
        pdf.cell(200, 6, txt="No processing steps recorded", ln=True)
    pdf.ln(10)
    
    # Section 3: Visualizations
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="3. Key Visualizations", ln=True)
    
    # Visualization 1: Distribution of first numeric column
    if numeric_cols:
        col = numeric_cols[0]
        plt.figure(figsize=(8, 4))
        sns.histplot(df[col], kde=True)
        plt.title(f"Distribution of {col}")
        plt.tight_layout()
        
        # Save plot to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        # Add image to PDF
        img_path = f"reports/{col}_dist_{file_id}.png"
        with open(img_path, 'wb') as f:
            f.write(buf.getbuffer())
        
        pdf.image(img_path, w=180)
        pdf.ln(5)
    
    # Visualization 2: Correlation heatmap (if multiple numeric columns)
    if len(numeric_cols) > 1:
        plt.figure(figsize=(10, 8))
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm')
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        
        # Save plot to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        # Add image to PDF
        img_path = f"reports/corr_heatmap_{file_id}.png"
        with open(img_path, 'wb') as f:
            f.write(buf.getbuffer())
        
        pdf.image(img_path, w=180)
        pdf.ln(5)
    
    # Section 4: Action History from Frontend
    if action_history:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="4. User Actions", ln=True)
        pdf.set_font("Arial", size=10)
        
        for action in action_history:
            pdf.cell(200, 6, txt=f"• {action}", ln=True)
        pdf.ln(10)
    
    # Save PDF
    pdf.output(report_path)
    return {
        "file_name": file_name,
        "shape": [df.shape[0], df.shape[1]],
        "timestamp": datetime.now().isoformat(),
        "report_url": f"/api/report/download/{file_id}",
        "steps": [
            {"title": "Data Overview", "description": "Initial data analysis"},
            {"title": "Data Cleaning", "description": "Missing value handling and normalization"},
            {"title": "Outlier Detection", "description": "Statistical outlier identification"},
            {"title": "Visualization", "description": "Key insights through charts"},
        ]
    }
