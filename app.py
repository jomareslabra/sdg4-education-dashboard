import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SDG 4 Education Dashboard", layout="wide")

# --- LOAD DATA ---
# Streamlit caches this so it doesn't reload the CSV every time you move the slider
@st.cache_data
def load_data():
    return pd.read_csv('cleaned_sdg4_data.csv')

df = load_data()

# --- SIDEBAR & TIME FILTER ---
st.sidebar.header("Dashboard Controls")
st.sidebar.write("Explore the drivers of Primary Education Completion (SDG 4).")

# Interactive time slider
min_year = int(df['Year'].min())
max_year = int(df['Year'].max())
selected_year = st.sidebar.slider("Select Year", min_value=min_year, max_value=max_year, value=max_year)

# Filter the dataset dynamically based on the slider
filtered_df = df[df['Year'] == selected_year]

# --- SIDEBAR: PREDICTIVE SIMULATOR ---
st.sidebar.markdown("---")
st.sidebar.header("What-If Simulator")
st.sidebar.write("Use the sliders to test how policy changes might impact global completion rates based on our regression model.")

# Create interactive sliders for the stakeholder to play with
sim_ptr = st.sidebar.slider("Hypothetical Pupil-Teacher Ratio", min_value=10.0, max_value=80.0, value=30.0)
sim_int = st.sidebar.slider("Hypothetical Internet Usage (%)", min_value=0.0, max_value=100.0, value=50.0)

# The Regression Math! 
# Y = Intercept + (Coef1 * X1) + (Coef2 * X2)
predicted_completion = 116.78 + (-1.12 * sim_ptr) + (-0.03 * sim_int)

# Cap the prediction at 100% for realistic display
predicted_completion = min(predicted_completion, 100.0)

st.sidebar.success(f"**Predicted Completion Rate: {predicted_completion:.1f}%**")

# --- MAIN DASHBOARD HEADER ---
st.title(f"Global Education Quality (SDG 4) in {selected_year}")
st.markdown("""
**Insights from Regression Analysis:** Our robust model indicates that classroom strain 
(Pupil-Teacher Ratio) is the strongest significant driver of completion rates. High ratios 
severely negatively impact student success. Interestingly, raw government expenditure showed 
no significant global correlation.
""")

# --- KPIs ---
st.subheader("Global Averages for Selected Year")
col1, col2, col3 = st.columns(3)

# Calculate metrics, handling potential empty data for a specific year gracefully
if not filtered_df.empty:
    avg_comp = filtered_df['Completion_Rate'].mean()
    avg_ptr = filtered_df['Pupil_Teacher_Ratio'].mean()
    avg_int = filtered_df['Internet_Usage'].mean()
    
    col1.metric("Avg Primary Completion Rate", f"{avg_comp:.1f}%")
    col2.metric("Avg Pupil-Teacher Ratio", f"{avg_ptr:.1f}")
    col3.metric("Avg Internet Usage", f"{avg_int:.1f}%")
else:
    st.warning("No data available for the selected year. Please adjust the slider.")

st.markdown("---")

# --- DYNAMIC VISUALIZATIONS ---

# --- 1. The Global Map (Country Comparison) ---
st.subheader("Global Primary School Completion Rates")

# Added an info box to explain the >100% anomaly and missing data
st.info("""
Rates Over 100%:** You may notice some countries exceed a 100% completion rate. This is because the World Bank uses a "Gross" calculation. If many older/delayed students finally graduate in a single year, the total number of graduates can temporarily exceed the population of theoretical graduation-age children.

Gray Countries: Nations in gray lack complete data for the selected year across all our driver variables (Completion, Budget, Internet, and Pupil-Teacher ratio).
""")

# Added height=700 to make the map massive
fig_map = px.choropleth(
    filtered_df, 
    locations="Country", 
    locationmode="country names", 
    color="Completion_Rate", 
    hover_name="Country",
    color_continuous_scale="Viridis",
    title=f"Completion Rates by Country ({selected_year})",
    height=700 
)

# This removes the extra white space around the map to make it even bigger
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

st.plotly_chart(fig_map, use_container_width=True)

# --- 1.2 DYNAMIC VISUALIZATIONS: TOP & BOTTOM PERFORMERS ---
st.subheader(f"Top and Bottom 10 Countries ({selected_year})")
st.write("A quick look at the highest and lowest primary completion rates for the selected year.")

if not filtered_df.empty:
    # Sort the data and grab the top 10 and bottom 10
    sorted_df = filtered_df.sort_values(by="Completion_Rate", ascending=False).dropna()
    top_10 = sorted_df.head(10)
    bottom_10 = sorted_df.tail(10)
    
    # Combine them for the chart
    extremes_df = pd.concat([top_10, bottom_10])
    
    # Create the Bar Chart
    fig_bar = px.bar(
        extremes_df, 
        x="Completion_Rate", 
        y="Country", 
        orientation='h',
        color="Completion_Rate",
        color_continuous_scale="RdYlGn",
        title="Top 10 vs Bottom 10 Completion Rates"
    )
    # This forces the chart to display the highest at the top
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 1.5 DYNAMIC VISUALIZATIONS: TRENDS OVER TIME ---
st.subheader("Historical Trends Over Time")
st.write("Select a specific country to view its historical progress, or leave it blank to see the global average.")

# Create a dropdown to select a country (optional, defaults to Global Average)
country_list = ["Global Average"] + list(df['Country'].unique())
selected_trend_country = st.selectbox("Select Country for Trend Line", country_list)

if selected_trend_country == "Global Average":
    # Group by year to get the global average for all metrics
    trend_df = df.groupby('Year')[['Completion_Rate', 'Pupil_Teacher_Ratio']].mean().reset_index()
    title_text = "Global Average: Primary Completion Rate Over Time"
else:
    # Filter the data for only the selected country
    trend_df = df[df['Country'] == selected_trend_country]
    title_text = f"{selected_trend_country}: Primary Completion Rate Over Time"

# Build the Line Chart
fig_trend = px.line(
    trend_df, 
    x="Year", 
    y="Completion_Rate", 
    title=title_text,
    markers=True,
    color_discrete_sequence=['#1f77b4']
)

# Add a secondary line for the main driver (Pupil-Teacher Ratio) to show the relationship
fig_trend.add_scatter(
    x=trend_df['Year'], 
    y=trend_df['Pupil_Teacher_Ratio'], 
    mode='lines+markers', 
    name='Pupil-Teacher Ratio',
    line=dict(dash='dot', color='red')
)

st.plotly_chart(fig_trend, use_container_width=True)

# --- 2. DYNAMIC VISUALIZATIONS: DEDICATED METRIC TABS ---
st.subheader("Driver Analysis: Exploring the Explanatory Variables")
st.write("Click through the tabs below to view the dedicated relationship between each key metric and the primary completion rate.")

# Create tabs for each explanatory variable (Gestalt Principle: Grouping)
tab1, tab2, tab3 = st.tabs(["📚 Pupil-Teacher Ratio", "🌐 Internet Usage", "💰 Gov. Expenditure"])

with tab1:
    st.write("**Impact of Educator Workload:** Higher ratios usually correlate with lower completion rates.")
    fig_ptr = px.scatter(filtered_df, x="Pupil_Teacher_Ratio", y="Completion_Rate", 
                         hover_name="Country", trendline="ols",
                         title=f"Pupil-Teacher Ratio vs. Completion Rate ({selected_year})")
    st.plotly_chart(fig_ptr, use_container_width=True)

with tab2:
    st.write("**Impact of Digital Access:** Exploring the digital divide.")
    fig_int = px.scatter(filtered_df, x="Internet_Usage", y="Completion_Rate", 
                         hover_name="Country", trendline="ols",
                         title=f"Internet Usage vs. Completion Rate ({selected_year})")
    st.plotly_chart(fig_int, use_container_width=True)

with tab3:
    st.write("**Impact of Financial Support:** Total government expenditure on education as a % of GDP.")
    fig_gov = px.scatter(filtered_df, x="Gov_Expenditure", y="Completion_Rate", 
                         hover_name="Country", trendline="ols",
                         title=f"Government Expenditure vs. Completion Rate ({selected_year})")
    st.plotly_chart(fig_gov, use_container_width=True)

# --- 3. DYNAMIC VISUALIZATIONS: CORRELATION HEATMAP ---
st.subheader("Statistical Correlation Matrix")
st.write("This heatmap shows how all our variables relate to one another across the entire dataset. A score close to 1 or -1 indicates a very strong relationship.")

# Select only the numerical columns for the correlation math
numeric_cols = df[['Completion_Rate', 'Pupil_Teacher_Ratio', 'Gov_Expenditure', 'Internet_Usage']]
corr_matrix = numeric_cols.corr()

# Create the Heatmap
fig_heat = px.imshow(
    corr_matrix, 
    text_auto=True, 
    aspect="auto",
    color_continuous_scale="RdBu_r",
    title="Variable Correlation Heatmap"
)
st.plotly_chart(fig_heat, use_container_width=True)