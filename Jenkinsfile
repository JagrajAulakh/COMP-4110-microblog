pipeline {
    agent any

    stages {
        stage('Clone repo') {
            steps {
                echo 'Cloning repo $GIT_URL on branch $GIT_BRANCH'
                checkout scmGit(branches: [[name: '*/master']], extensions: [], userRemoteConfigs: [[credentialsId: 'b082c69a-5eb6-4f94-ab2d-c9d9c5c93ef2', url: 'git@github.com:JagrajAulakh/COMP-4110-microblog.git']])
            }
        }
        stage('build') {
            steps {
                sh 'docker-compose build'
            }
        }
        stage('deploy') {
            steps {
                sh 'docker-compose down || true'
                sh 'docker-compose up -d'
            }
        }
    }
    post {
        always {
            discordSend description: "Microblog Jenkins Build", footer: "A build job just ran in Jenkins to build the Microblog web appliation", link: "https://microblog.jagrajaulakh.com", result: currentBuild.currentResult, title: JOB_NAME, webhookURL: "https://discord.com/api/webhooks/1075270335785607218/AOp1vqfvrOxApQXw4TsBUUM0aU17otr8UCuRLeprRJJ--yYxD516IJDgrSElhHsnaQYm"
        }
    }
}

