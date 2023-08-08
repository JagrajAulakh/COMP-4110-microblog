pipeline {
	agent any

		stages {
			stage('build') {
				steps {
					sh 'docker-compose build'
				}
			}
			stage('test') {
				steps {
					echo 'Running pytest unit tests'
					sh 'docker container rm microblog-tests || true'
					sh 'docker run -t --name microblog-tests -e TESTING=true microblog sh boot.sh'
				}
			}
			stage('deploy') {
				steps {
					sh 'docker-compose up -d'
				}
			}
		}
}

