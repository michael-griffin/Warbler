## Warbler

A twitter clone where users can like messages and follow other users.


#### Login:

**Username: guest** <br>
**Password: password** <br>


### Local Setup

1. Navigate to base directory. Create virtual environment and activate.

  ```Shell
  python3 -m venv venv
  source venv/bin/activate
  ```

2. Install dependencies.

  ```Shell
  pip3 install -r requirements.txt
  ```

3. Setup database
  Create a .env file, with contents
  ```
  `DATABASE_URL=postgresql:///warbler`
  ```
  Run `seed.py` to create database

4. Running the App
  ```Shell
  flask run
  ```

5. Run tests
  To generate and see coverage report, run:
  ```Shell
  coverage run -m pytest #runs coverage suite
  coverage html #writes HTML to htmlcov/ with results
  ```
