Kuiren Su
1435683571 
Run Client.py with command:
	python2.7 Client.py –s serverIP –p portno –l logfile –n clientName
Run Server.py with command:
	python2.7 Server.py –p portno –l logfile -h handler
SpawnedClient.py is called by Server.py. When a unregistered client is spawned, Server instantiate a spawnedClient object and passes arguments to this spawnedClient. 