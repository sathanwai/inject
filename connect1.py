import pxssh
    import getpass
    try:                                                            
        s = pxssh.pxssh()
        hostname = raw_input('hostname: ')
        username = raw_input('username: ')
        password = getpass.getpass('password: ')
        s.login (hostname, username, password)
        s.sendline ('uptime')  # run a command
        s.prompt()             # match the prompt
        print s.before         # print everything before the prompt.
        s.sendline ('ls -l')
        s.prompt()
        print s.before
        s.sendline ('df')
        s.prompt()
        print s.before
        s.logout()
    except pxssh.ExceptionPxssh, e:
        print "pxssh failed on login."
        print str(e)
 
Note that if you have ssh-agent running while doing development with pxssh
then this can lead to a lot of confusion. Many X display managers (xdm,
gdm, kdm, etc.) will automatically start a GUI agent. You may see a GUI
dialog box popup asking for a password during development. You should turn
off any key agents during testing. The 'force_password' attribute will turn
off public key authentication. This will only work if the remote SSH server
is configured to allow password logins. Example of using 'force_password'
attribute::
 
        s = pxssh.pxssh()
        s.force_password = True
        hostname = raw_input('hostname: ')
        username = raw_input('username: ')
        password = getpass.getpass('password: ')
        s.login (hostname, username, password)