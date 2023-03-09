## Geoserver Installation Guide

This guide assumes Debian-based OS.

## Contents
 - [Stack Summary](#stack-summary) 
 - [Installation](#installation)
    1. Tomcat
    2. Apache
    3. Geoserver 
 - [Troubleshooting](#troubleshooting)
    1. Log Locations
    2. Restarting Services  
 - Configurations
    1. Geoserver - Enable CORS

## Stack Summary

- Java OpenJDK 11
  - Install Directory:  __/usr/lib/jvm/java-1.11.0-openjdk-amd64/__
- [Tomcat](#tomcat) v9.0.65
    - Install Directory:  __/opt/tomcat/__
- [Apache Web Server](#apache)
    - Install Directory: __/etc/apache2/__
- [Geoserver](#geoserver) v2.20
    - Standlone servlet installed in tomcat webapps folder (see Geoserver installation steps for details)
- [Certbot](#certbot) for SSL certificate and HTTPS configuration

## Installation

- ### **Tomcat**
  
  1.  **Install Java**
        ```
        $ sudo apt update
        $ sudo apt install openjdk-11-jdk
        ```

  2. **Create Tomcat User**
     1. Create Tomcat Group
   
        ```
        $ sudo groupadd tomcat
        ```

     2. Create tomcat user
   
        ```
        $ sudo useradd -s /bin/false -g tomcat -d /opt/tomcat tomcat
        ```

  3. **Install Tomcat**
     1. Download the Tomcat 9 archive, saving it to the /tmp folder
        ```
        $ cd /tmp
        $ curl -O http://www-eu.apache.org/dist/tomcat/tomcat-9/v9.0.11/bin/apache-tomcat-9.0.11.tar.gz
        ```
     2.  Extract the archive contents
            ```
            $ sudo mkdir /opt/tomcat &&
            $ sudo tar xzvf apache-tomcat-9*tar.gz -C /opt/tomcat --strip-components=1
            ```
    1. **Update Permissions**
   
        1. Give tomcat group ownership of install directory
            ```
            $ cd /opt/tomcat
            $ sudo chgrp -R tomcat /opt/tomcat
            ```
        2. Configure tomcat permissions 
            ```
            $ sudo chmod -R g+r conf
            $ sudo chmod g+x conf
            $ sudo chown -R tomcat webapps/ work/ temp/ logs/
            ```

    2. **Create systemd service for tomcat**
        1. Create service file
            ```
            $ sudo vim /etc/systemd/system/tomcat.service
            ``` 
        2. Copy/paste and save the following into the newly created service file (**Note**: Update JAVA_HOME if your jdk version or installation location differs)
            ```
            [Unit]
            Description=Apache Tomcat Web Application Container
            After=network.target

            [Service]
            Type=forking

            Environment=JAVA_HOME=/usr/lib/jvm/java-1.11.0-openjdk-amd64
            Environment=CATALINA_PID=/opt/tomcat/temp/tomcat.pid
            Environment=CATALINA_HOME=/opt/tomcat
            Environment=CATALINA_BASE=/opt/tomcat
            Environment='CATALINA_OPTS=-Xms512M -Xmx1024M -server -XX:+UseParallelGC'
            Environment='JAVA_OPTS=-Djava.awt.headless=true -Dorg.geotools.referencing.forceXY=true -Dorg.geotools.localDateTimeHandling=true -Djava.security.egd=file:/dev/./urandom'

            ExecStart=/opt/tomcat/bin/startup.sh
            ExecStop=/opt/tomcat/bin/shutdown.sh

            User=tomcat
            Group=tomcat
            UMask=0007
            RestartSec=10
            Restart=always

            [Install]
            WantedBy=multi-user.target
            ```
        3. Reload the systemd daemon and start the tomcat service
            ```
            $ sudo systemctl daemon-reload
            $ sudo systemctl start tomcat
            ```

        4. Enable the service file so tomcat automatically starts at boot
            ```
            $ sudo systemctl enable tomcat
            ```

    3. **Define AJP Connector**
   
        1. Open the tomcat file **server.xml**
            ```
            $ sudo vim /opt/tomcat/conf/server.xml
            ```
        2.  Add the following (Be sure to create your own password)
            ```
            <Connector protocol="AJP/1.3"
                secretRequired="true"
                secret="<SET A PASSWORD HERE>"
                port="8009"
                redirectPort="8443"
            />
            ```
- ### **Apache**

  1.  **Install with apt**

        This will automatically create and start a systemd service for apache
        ```
        $ sudo apt install apache2
        ```

  2. **Check server status**

        ```
        $ sudo systemctl status apache2
        ```

        At this point you can enter the server's ip in your browser. You should see the Apache2 default splash page. 

 1. **Enabled the AJP proxy module**

        ```
        $ sudo a2enmod proxy_ajp
        $ sudo systemctl restart apache2
        ```

 2. **Set up your virtual host**
    
    1. Open the default virtual host configuration file
        ```
        $ sudo vim /etc/apache2/sites-enabled/000-default.conf
        ```

    2. Copy/paste and following virtualhost configuration:
        
        **IMPORTANT -** Replace any instance where you see **\<AJP TOMCAT PASSWORD>** below with the password you defined in the **Define AJP Connector** step of the [Tomcat](#tomcat) installation 
        ```
        <VirtualHost *:80>
            # The ServerName directive sets the request scheme, hostname and port that
            # the server uses to identify itself. This is used when creating
            # redirection URLs. In the context of virtual hosts, the ServerName
            # specifies what hostname must appear in the request's Host: header to
            # match this virtual host. For the default virtual host (this file) this
            # value is not decisive as it is used as a last resort host regardless.
            # However, you must set it for any further virtual host explicitly.
            ServerName geoserver.ice-d.org
            ServerAlias www.geoserver.ice-d.org
            ServerAdmin webmaster@localhost
            DocumentRoot /var/www/html

            ErrorLog ${APACHE_LOG_DIR}/error.log
            CustomLog ${APACHE_LOG_DIR}/access.log combined

            ProxyRequests Off
            <Proxy *>
                Order deny,allow
                Allow from all
            </Proxy>

            ProxyPass /geoserver ajp://localhost:8009/geoserver secret=<AJP TOMCAT PASSWORD>
            ProxyPass / ajp://localhost:8009/geoserver secret=<AJP TOMCAT PASSWORD>
            ProxyPassReverse / http://localhost:8009/geoserver

            <Location />
                Order allow,deny
                Allow from all
            </Location>

            ProxyPreserveHost On

            RewriteEngine on
            RewriteCond %{SERVER_NAME} =geoserver.ice-d.org [OR]
            RewriteCond %{SERVER_NAME} =www.geoserver.ice-d.org
            RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
        </VirtualHost>
        ```

    3. Restart the apache service
        
        This is required after any changes made to the apache configuration.
        ```
        $ sudo systemctl restart apache
        ```


- ### **Geoserver**
  
    The Geoserver documentation offers two ways to install the server:
    1. As a servlet to use on Apache Tomcat [Documentation](https://docs.geoserver.org/latest/en/user/installation/linux.html)
    2. As a binary bundled with Jetty [Documentation](https://docs.geoserver.org/stable/en/user/installation/war.html#installation-war)


    The Geoserver was was initially installed as the lightweight binary bundled with Jetty. For a more production-ready configuration:
    1. Tomcat and Apache were installed.
    2. The geoserver servlet was installed in tomcat webapps folder (**/opt/tomcat/webapps**). When you save the geoserver war file a new geoserver directory will automatically appear. You will need to access files in new directory in the next step.
    3. In order to preserve development changes, the data directory of the new tomcat geoserver instance was pointed to the initial instance.
        ```
        $ sudo vim /opt/tomcat/webapps/geoserver/WEB-INF/web.xml
        ```
        Add the following:
        ```
        <context-param>
            <param-name>GEOSERVER_DATA_DIR</param-name>
            <param-value>/usr/share/geoserver/data_dir</param-value>
        </context-param>
        ```
        Note that the data directory can be changed to any other location by updating this parameter

- ### **Certbot**
    Certbot provides a fast and easy method to generate an ssl certification for your server and to set up the virtual host on port 443 for your apache server.

    Follow the [instructions](https://certbot.eff.org/instructions?ws=apache&os=debianbuster) to run certbot on a debian/apache set-up.

    Once you've successfully completed the steps you will see a new file in the apache directory under **/sites-enabled**. The server will now automatically reroute 80 requests to 443.

## Troubleshooting

  1. Log locations
     1. Apache: **/var/log/apache2/**
     2. Tomcat: **/opt/tomcat/logs/**
     3. Geoserver: **/usr/share/geoserver/data_dir/logs/geoserver.log[.#]**

  2. Restarting services
   
     The geoserver can be restarted by restarting the tomcat service:
     ```
     $ sudo systemctl restart tomcat
     ```

     Same method for apache2:
     ```
     $ sudo systemctl restart apache2
     ```


## Configurations

  1. Geoserver - Enable CORS

        To enable CORS, uncomment the following from **/opt/tomcat/webapps/geoserver/WEB-INF/web.xml** and restart tomcat.

        ```
        <filter>
            <filter-name>cross-origin</filter-name>
            <filter-class>org.apache.catalina.filters.CorsFilter</filter-class>
            <init-param>
                <param-name>cors.allowed.origins</param-name>
                <param-value>*</param-value>
            </init-param>
            <init-param>
                <param-name>cors.allowed.methods</param-name>
                <param-value>GET,POST,PUT,DELETE,HEAD,OPTIONS</param-value>
            </init-param>
            <init-param>
                <param-name>cors.allowed.headers</param-name>
                <param-value>*</param-value>
            </init-param>
        </filter>
        ```
        ```
        <filter-mapping>
            <filter-name>cross-origin</filter-name>
            <url-pattern>/*</url-pattern>
        </filter-mapping>
        ```
