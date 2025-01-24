# AutoLogin and Order Details Extractor for Sainsbury's

This project automates the process of logging into a Sainsbury's account, navigating to the orders page, and extracting the details of each order into a text file. The extracted files are saved in a structured manner within a specified folder.

## Features

- **Automated Login**: Automatically logs into your Sainsbury's account using credentials stored securely in an `.env` file.
- **Cookie Handling**: Automatically accepts cookies to streamline navigation.
- **Order Extraction**: Extracts and saves details of each order from the "My Orders" section.
- **Error Handling**: Includes robust exception handling for a smooth execution process.
- **Organized Storage**: Saves order details as individual text files in a dedicated folder.

## Prerequisites

- Python 3.8+
- Google Chrome (ensure the installed version matches the version of ChromeDriver used)
- ChromeDriver (installed via pip or manually)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/iron-66/Ebyer_Autologin
   cd Ebyer_Autologin
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following content:
   ```env
   SAINSBURYS_USERNAME=your_email@example.com
   SAINSBURYS_PASSWORD=your_password
   ```

4. Verify ChromeDriver installation:
   - Install via pip:
     ```bash
     pip install chromedriver-py
     ```
   - Alternatively, download manually from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads) and ensure it matches your Chrome version.

## Usage

1. Run the script:
   ```bash
   python main.py
   ```

2. The script will:
   - Log in to your Sainsbury's account.
   - Navigate to the "My Orders" page.
   - Click on each order and extract its details.
   - Save the extracted details as `.txt` files in a folder named `order_details`.

## Folder Structure

```
.
├── autologin
│   ├── main.py         # Main script
│   └── .env            # Environment variables (not included in the repository)
├── order_details       # Folder for saving extracted orders (created dynamically)
├── requirements.txt    # Python dependencies
└── README.md           # Project description
```

## Example Output

After running the script, the `order_details` folder will contain files like:

```
order_details/
├── order_1.txt
├── order_2.txt
├── order_3.txt
└── ...
```

Each file contains the details of a specific order, formatted for readability.

## Dependencies

- `selenium`
- `python-dotenv`

Install these dependencies using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

