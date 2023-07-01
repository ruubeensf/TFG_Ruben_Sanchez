
build:
	docker build -t teamwork_api .

run:
	docker run -d -p 5000:5000 --name teamwork_api_container teamwork_api
