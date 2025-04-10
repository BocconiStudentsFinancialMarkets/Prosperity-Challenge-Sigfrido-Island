# %%
import pandas as pd
def organize_file(input_file_path,output_file_path):

    columns = [
    "day", "timestamp", "product", 
    "bid_price_1", "bid_volume_1", "bid_price_2", "bid_volume_2", "bid_price_3", "bid_volume_3",
    "ask_price_1", "ask_volume_1", "ask_price_2", "ask_volume_2", "ask_price_3", "ask_volume_3",
    "mid_price", "profit_and_loss"
    ]


    df = pd.read_csv(input_file_path, header=None, names=["raw_data"])
    split_data = df["raw_data"].str.split(";", expand=True)
    split_data.columns = columns
    split_data.to_csv(output_file_path, index=False)
    print(f"file saved to {output_file_path}")
    

# %%
import glob
import os

folder_path = 'D:/!BOCCONI STUDY/prosperity challenge/BOTTLE_DATA_TRANSFORMED/'
all_files = glob.glob(f"{folder_path}/*.csv")

for file in all_files:
    file_name = os.path.basename(file)
    file_name_no_ext = os.path.splitext(file_name)[0]
    new_file_name=file_name_no_ext+"ORGANIZED"+".csv"
    output_file_path = os.path.join(folder_path, new_file_name)
    organize_file(file,output_file_path)

# %%
#combining all the data in one file:
import pandas as pd
import glob
import os

folder_path = 'D:/!BOCCONI STUDY/prosperity challenge/BOTTLE_DATA_TRANSFORMED/New folder'
all_files = glob.glob(f"{folder_path}/*ORGANIZED.csv")

df_list = []

for file in all_files:
    df = pd.read_csv(file)
    df_list.append(df)

# sorting them from day -2,-1,0
combined_df = pd.concat(df_list, ignore_index=True)
combined_df.sort_values(by=['day', 'timestamp'], inplace=True)
combined_df.to_csv('D:/!BOCCONI STUDY/prosperity challenge/BOTTLE_DATA_TRANSFORMED/New folder/combined_data.csv', index=False)
# Display the first few rows to verify
print(combined_df.head())
# %%
#imports for training the  model
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
#%%
# Load your data
file_path = 'D:/!BOCCONI STUDY/prosperity challenge/BOTTLE_DATA_TRANSFORMED/New folder/combined_data.csv'
df = pd.read_csv(file_path)

# Convert to numeric
df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
df['mid_price'] = pd.to_numeric(df['mid_price'], errors='coerce')
df['bid_price_1'] = pd.to_numeric(df['bid_price_1'], errors='coerce')
df['profit_and_loss'] = pd.to_numeric(df['profit_and_loss'], errors='coerce')

# Drop rows with missing values for relevant columns
df.dropna(subset=['mid_price', 'timestamp', 'bid_price_1'], inplace=True)

# List of unique products
products = df['product'].unique()

# Dictionary to store models and their performance
models = {}
results = {}

for product in products:
    # Filter data for the specific product
    product_df = df[df['product'] == product]

    # Define features and target
    features = [
        'timestamp', 'day', 'bid_price_1', 'bid_volume_1',
        'ask_price_1', 'ask_volume_1', 
    ]
    
    X = product_df[features]
    y = product_df['mid_price']

    # Train-test split (no shuffle to preserve time sequence)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    # Train the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    models[product] = model  # Store the trained model

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate the model
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Store results
    results[product] = {'mse': mse, 'r2': r2}

    # Print performance metrics
    print(f"\nModel Performance for {product}:")
    print(f"Intercept: {model.intercept_}")
    print(f"Coefficients: {model.coef_}")
    print(f"Mean Squared Error: {mse}")
    print(f"R² Score: {r2}")

    # Plotting results
    plt.figure(figsize=(10, 6))
    plt.plot(X_test['timestamp'], y_test, label='Actual Mid Price', color='blue')
    #plt.plot(X_test['timestamp'], y_pred, label='Predicted Mid Price', color='red')
    plt.title(f'{product} - Mid Price Prediction Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Mid Price')
    plt.legend()
    plt.show()
# %%
#trying to predict data for the future:
