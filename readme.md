FTP Server and Client Running instructions:

FTP Client-
To run the client, from the root directory, where the file is located do “python3 ftp_client.py”, this will run the client from the default ‘host’ and ‘port’. You must log in to use the client. 
To run on a different host, do “python3 fpt_client [HostName] [User] [Password]”. This will log you in as the specified user. 
When the client is running, you can prompt “help” to get a list of working commands. Fallow the help basic commands description to use the command properly.

FTP Server
To run the server, from the root directory, where the file is located do “python3 ftp_server.py”. This will run the Server from the specified Port.
To change configuration values, use a text editor and open the file located at [~/ftpserver/conf/fsys.cfg]. changes to values must be done before running the server.
For FTP user, the file located at [~/ftpserver/conf/users.cfg] contains a list of the users, their passwords and their privilege (user, admin).
Ex:
Username1 password2 admin
If a user is added to the server, the correct file directory must be created. Located at [~/ftpserver/ftproot/”username”]. 
