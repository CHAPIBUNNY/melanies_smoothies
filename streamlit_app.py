# Import necessary packages
import requests  # Moved here as per requirement
import streamlit as st
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Input for name on order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Initialize Snowflake session and retrieve fruit options
cnx = st.connection("snowflake")
session = cnx.session()

# Retrieve fruit data and convert to Pandas DataFrame
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'), col('SEARCH_ON')
).to_pandas()

# Debugging: Show the DataFrame content
st.dataframe(my_dataframe, use_container_width=True)
st.stop()  # Pause here for debugging

# Convert Snowpark DataFrame to Pandas
pd_df = my_dataframe

# Multiselect for ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# Button to submit order
time_to_insert = st.button('Submit Order', key="submit_button")

# Build and submit the SQL insert query if the button is clicked
if time_to_insert:
    if ingredients_list and name_on_order:
        ingredients_string = " ".join(ingredients_list)
        my_insert_stmt = f"""
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!")
    elif not name_on_order:
        st.warning("Please enter the name for your Smoothie before submitting.")
    elif not ingredients_list:
        st.warning("Please select at least one ingredient before submitting.")

# Additional logic to fetch and display fruit data
if ingredients_list:
    for fruit_chosen in ingredients_list:
        # Fetch SEARCH_ON value dynamically
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write(f"The search value for {fruit_chosen} is {search_on}.")

        # Fetch and display nutrition information
        st.subheader(f"{fruit_chosen} Nutrition Information")
        fruityvice_response = requests.get(f"https://fruityvice.com/api/fruit/{search_on}")
        if fruityvice_response.status_code == 200:
            sf_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)
        else:
            st.error(f"Failed to fetch data for {fruit_chosen}. API response: {fruityvice_response.status_code}")
