# Import python packages
import pandas as pd
import streamlit as st
from snowflake.snowpark.functions import col
import requests

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

# Get customer's name
name_on_order = st.text_input('Name on Smoothie:')

st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit options from Snowflake
my_dataframe = session.table(
    "smoothies.public.fruit_options"
).select(
    col('FRUIT_NAME'),
    col('SEARCH_ON')
)

# Convert Snowpark DataFrame to Pandas DataFrame
pd_df = my_dataframe.to_pandas()

#st.dataframe(pd_df)

# Temporarily stop the app to inspect the dataframe
#st.stop()

# Allow customers to select up to 5 fruits
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

# Display nutrition information for selected fruits
if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Display nutrition information for each selected fruit
        st.subheader(fruit_chosen + ' Nutrition Information')
        try:
            search_on = session.table(
                "smoothies.public.fruit_options"
            ).filter(
                col("FRUIT_NAME") == fruit_chosen
            ).select("SEARCH_ON").collect()[0]["SEARCH_ON"]
            st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')
            smoothiefroot_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{search_on.lower()}",
            timeout=10
            )

            smoothiefroot_response.raise_for_status()
            sf_data = smoothiefroot_response.json()

            if "error" in sf_data:
                st.warning(
                    f"Nutrition information is unavailable for {fruit_chosen}."
                )
            else:
                st.dataframe(
                    data=sf_data,
                    use_container_width=True
                )

        except requests.exceptions.RequestException:
            st.warning(
                f"Could not retrieve nutrition information for {fruit_chosen}."
            )

    # Prepare the order insertion statement
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(
            my_insert_stmt,
            params=[ingredients_string.strip(), name_on_order]
        ).collect()

        st.success(
            'Your Smoothie is ordered, ' + name_on_order + '!',
            icon="✅"
        )
