# Import necessary packages
import requests  # For API calls
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

# Multiselect for ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    my_dataframe['FRUIT_NAME'].tolist(),
    max_selections=5
)

# Display selected fruits with SEARCH_ON values and fetch data
if ingredients_list:
    for fruit_chosen in ingredients_list:
        # Fetch SEARCH_ON value dynamically and apply fallback
        search_on = my_dataframe.loc[my_dataframe['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        if not search_on or search_on == "None":
            search_on = fruit_chosen.lower()  # Fallback to fruit name in lowercase
        
        #st.write(f"The search value for **{fruit_chosen}** is **{search_on}**.")

        # Display nutrition information
        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        if response.status_code == 200:
            # Display nutrition information in a table
            st.dataframe(response.json(), use_container_width=True)
        else:
            st.error(f"Failed to fetch data for {fruit_chosen}. API response: {response.status_code}")

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
