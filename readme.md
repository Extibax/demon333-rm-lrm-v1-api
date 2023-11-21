# Local Retail Management API

1. install pip dependencies `pip install -r requirements.txt`.
2. For linux do, execute the following commands before step 3:

   1. `sudo apt install python3-dev build-essential`
   2. `sudo apt install libssl1.1`
   3. `sudo apt install libssl1.1=1.1.1f-1ubuntu2`
   4. `sudo apt install libssl-dev`
   5. `sudo apt-get install libmysqlclient-dev`
   6. `sudo apt-get install python3-tk`

3. Set up .env.environment_name file
4. Run server with :
   - if youre on linux run`export PYTHON_ENV=dev && python manage.py runserver`
   - if youre on windows run:
     - `$env:PYTHON_ENV = 'dev'`
     - `python manage.py runserver`

## Docker set up

### Build

1. Build the docker image with: `docker build -t lrm-api .`

2. Test docker image with: `docker run --name lrm -p 80:80 --env-file .env.dev lrm-api`

### Push image to ECR

if youre on linux machine be sure to create gpg keys with: `gpg --generate-key` copy the pub hex and then `pass init _hexkey_`

1. Login to ECR with: `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 185279236646.dkr.ecr.us-east-1.amazonaws.com`

2. Create a repository in ECR and get its URI

3. Tag local image: `docker tag lrm-api 185279236646.dkr.ecr.us-east-1.amazonaws.com/local-retail-management`

4. Push image with `docker push 185279236646.dkr.ecr.us-east-1.amazonaws.com/local-retail-management`

5. Set up ECS Tasks
