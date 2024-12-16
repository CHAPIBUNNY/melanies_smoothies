# Import necessary packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col, when_matched  # Added when_matched

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

# Input for name on order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Initialize Snowflake session and retrieve fruit options
cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME')).to_pandas()
fruit_options = my_dataframe['FRUIT_NAME'].tolist()  # Convert to a list for multiselect

# Multiselect for ingredients
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5
)

# Handle ingredients logic
if ingredients_list:
    ingredients_string = ''
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '
        smoothiefroot_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{fruit_chosen}"
        )
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)

# Button to submit order
time_to_insert = st.button('Submit Order', key="submit_button")

# Build and submit the SQL insert query if the button is clicked
if time_to_insert:
    if ingredients_list and name_on_order:
        # Create a single string from the selected ingredients
        ingredients_string = ", ".join(ingredients_list)
        
        # Build the SQL insert query
        my_insert_stmt = f"""
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        
        # Execute the query
        session.sql(my_insert_stmt).collect()
        
        # Show success message
        st.success(f"Your Smoothie for is ordered, {name_on_order}!")
    elif not name_on_order:
        st.warning("Please enter the name for your Smoothie before submitting.")
    elif not ingredients_list:
        st.warning("Please select at least one ingredient before submitting.")

# Merge logic to update ORDER_FILLED where necessary
try:
    # Retrieve the current orders and edited data
    og_dataset = session.table("smoothies.public.orders")
    edited_dataset = session.create_dataframe(my_dataframe)  # Replace with edited_df if available
    
    # Perform the merge to update ORDER_FILLED
    og_dataset.merge(
        edited_dataset,
        (og_dataset['ORDER_UID'] == edited_dataset['ORDER_UID']),
        [when_matched().update({'ORDER_FILLED': edited_dataset['ORDER_FILLED']})]
    )

    st.success("Order updates merged successfully!", icon="✅")
except Exception as e:
    st.error(f"Failed to update orders: {e}")
