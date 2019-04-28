# Item Catalog Application
It is a catalog application to retrieve, add, update and delete items from
different categories. This project was prepared as part of Udacity Full-Stack Nanodegree program.

# Requirements and Installation

1. Install VirtualBox (https://www.virtualbox.org/)
2. Install Vagrant tool (https://www.vagrantup.com/)
3. Install Python 2.7(https://www.python.org/)
4. Git Bash terminal(for windows machines only)(https://git-scm.com/downloads)


# Running the project
In order to get this project running, you need to follow these steps:

  1. Clone or download the project to the vagrant folder you have after installation .
  2. Open terminal and go to the vagrant folder.
  3.  Launch Vagrant to set up the virtual machine and then log into the virtual machine by executing the following:
      vagrant up
      vagrant ssh
  3. Go inside the catalog folder by executing:
      cd /vagrant/catalog

  4. Generate and fill the database by executing the following command in the terminal:
        python fillDB.py
  5. Run the application by executing the following command:
      python views.py
  6. Go to http://localhost:5000/ and enjoy the application
