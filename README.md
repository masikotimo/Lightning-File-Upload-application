# Lightning-File-Upload-application
File upload application  offers you space to upload your files for a few sats 


The MVP objectives are :

- Registration 
- Login
- Deposit sats 
- Upload files 


## Developer Setup

Create a new python virtual env (>=3.9 preferably, but _may_ work with lower versions). Install the requirements into that environment with pip

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file from the `.env.example` file in the project root directory. Customise the values to fit your scenario. For purely local development, you  strictly need to update all the fields in that file:



## Running the application

Run any pending migrations and start the application

```bash
flask run
```

## The Feedback gotten from the demos :

- Ability for one to deposit sats per file upload   
- Be able to view the files after upload 
- Avoid the file service from directly removing funds (leave the authority to the user)
- Drag and drop feature
 