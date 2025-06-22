import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from state import data_store
import pandas as pd
import logging
import warnings

# Configure logging
logger = logging.getLogger(__name__)

# Suppress seaborn/pandas deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Print version info for debug
print("Pandas version:", pd.__version__)
print("Seaborn version:", sns.__version__)
print("Matplotlib version:", matplotlib.__version__)

def generate_visualization(file_id, chart_type, x_col, y_col=None, hue_col=None):
    try:
        # Convert empty strings to None
        if y_col == "":
            y_col = None
        if hue_col == "":
            hue_col = None

        # Retrieve dataframe
        if file_id not in data_store:
            logger.error(f"File ID '{file_id}' not found in data store")
            return None

        df_entry = data_store[file_id]

        # Determine if full or simplified storage
        if isinstance(df_entry, dict) and "current_df" in df_entry:
            df = df_entry["current_df"]
        elif isinstance(df_entry, pd.DataFrame):
            df = df_entry
        else:
            logger.error("Invalid data structure for file ID")
            return None

        # Validate column names
        if x_col not in df.columns:
            raise ValueError(f"Column '{x_col}' not found in data")
        if y_col and y_col not in df.columns:
            raise ValueError(f"Column '{y_col}' not found in data")
        if hue_col and hue_col not in df.columns:
            raise ValueError(f"Column '{hue_col}' not found in data")

        plt.figure(figsize=(12, 8))

        # Plot settings
        plot_kwargs = {}
        if hue_col:
            plot_kwargs["hue"] = hue_col

        # Generate chart based on type
        if chart_type == "bar":
            if not y_col:
                raise ValueError("Y-axis column required for bar chart")
            sns.barplot(data=df, x=x_col, y=y_col, **plot_kwargs)

        elif chart_type == "line":
            if not y_col:
                raise ValueError("Y-axis column required for line chart")
            sns.lineplot(data=df, x=x_col, y=y_col, **plot_kwargs)

        elif chart_type == "scatter":
            if not y_col:
                raise ValueError("Y-axis column required for scatter plot")
            sns.scatterplot(data=df, x=x_col, y=y_col, **plot_kwargs)

        elif chart_type == "histogram":
            sns.histplot(data=df, x=x_col, kde=True, **plot_kwargs)

        elif chart_type == "box":
            if not y_col:
                raise ValueError("Y-axis column required for box plot")
            sns.boxplot(data=df, x=x_col, y=y_col, **plot_kwargs)

        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        plt.title(f"{chart_type.capitalize()} of {x_col}" + (f" vs {y_col}" if y_col else ""))
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save chart to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return buf

    except Exception as e:
        logger.exception(f"Visualization error: {str(e)}")
        raise ValueError(f"Chart generation failed: {str(e)}")
