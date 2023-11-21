docker build -t lrm-api .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 185279236646.dkr.ecr.us-east-1.amazonaws.com
docker tag lrm-api 185279236646.dkr.ecr.us-east-1.amazonaws.com/lrm-v2-prod-api
docker push 185279236646.dkr.ecr.us-east-1.amazonaws.com/lrm-v2-prod-api
python3 scripts.py prod