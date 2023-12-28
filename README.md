# Warbler

A twitter clone where users can like messages and follow other users.

Deployed on: http://www.warbler.michaellngriffin.com <br>
**Username: guest** <br>
**Password: password** <br>

<br>

### Built with

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
- ![postgresql](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)

<br>

## Local Setup

1. Navigate to base directory. Create virtual environment and activate.

  ```Shell
  python3 -m venv venv
  source venv/bin/activate
  ```

2. Install dependencies.

  ```Shell
  pip3 install -r requirements.txt
  ```

3. Setup database <br>
  Create a .env file, with contents
  ```
  `DATABASE_URL=postgresql:///warbler`
  ```

4. Run `seed.py` to create database

<br>

## Running the App

Within the virtual environment, can start app with:
  ```Shell
  flask run
  ```
<br>

To generate and see coverage report, run:
  ```Shell
  coverage run -m pytest #runs coverage suite
  coverage html #writes HTML to htmlcov/ with results
  ```
