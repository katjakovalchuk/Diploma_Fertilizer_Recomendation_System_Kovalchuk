# Research on the Effectiveness of Differentiated Farming and Development of a Fertilizer Recommendation System

Student: Kateryna Kovalchuk [LinkedIn](https://www.linkedin.com/in/katkovalchuk/)

Thesis Advisor: Taras Firman [LinkedIn](https://www.linkedin.com/in/taras-firman-752684b8/)


A web application that recommends fertilizers based on simulation results using user-provided data: soil chemical analysis, target crop yield, field area, preferred fertilizer type, etc.

The project includes a PostgreSQL database, simulation and recommendation logic (Python/Flask), and a user interface (HTML, CSS, JavaScript).

## Requirements

- Python 3.12.8
- PostgreSQL 18

## Setup

### 1. Install Python dependencies

```cmd
pip install -r requirements.txt
```

### 2. Install PostgreSQL

1. Go to [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) and click **Download the installer** button
2. Choose version 18+ for **Windows x86-64** and download it
3. Run the installer and follow the instructions
4. When prompted to create a password for the `postgres` user — **set and remember it**, you will need it later
5. Leave the default port `5432` unchanged

### 3. Create and restore the database

Open **cmd** and run the following commands.

Create the database:
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -c "CREATE DATABASE fertilizer_recommendation_db;"
```

Restore the database from the dump (replace `path_to_this_repository` with the actual path):
```cmd
"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres -d fertilizer_recommendation_db -f "path_to_this_repository\Diploma_Fertilizer_Recommendation_System_Kovalchuk\web_app\data_base\database.sql"
```

Both commands will ask for the `postgres` user password — enter the one you set during installation.

### 4. Configure the database connection

Open `web_app\data_base\connection.py` and set the correct password for the `postgres` user in the `password` parameter:

---

## Running the App

1. Open a terminal and navigate to the `web_app` folder:
   ```cmd
   cd web_app
   ```

2. Start the application:
   ```cmd
   flask --app main run
   ```

3. Open the URL shown in the console:
   ```
   http://127.0.0.1:5000
   ```

---

## Troubleshooting

**Page shows "Not Found"** — add `/diploma/fertilizer_recommendation` to the end of the URL in your browser.

**Creating a field takes too long and the next page never loads** — reload the page and enter a field name that doesn't already exist in the database.

**Database connection error** — make sure the database name is `fertilizer_recommendation_db` and the password in `connection.py` matches the one set during PostgreSQL installation. User needs to be `postgres`. If you changed something while creating an account in PostgreSQL, you need to change corresponding parameter in `web_app\data_base\connection.py`.