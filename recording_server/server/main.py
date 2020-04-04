import datetime
import logging
from server.include.worker import ControlPrompt 

 # Create Logger / Log Handler
log_level = logging.DEBUG
log = logging.getLogger()
log.setLevel(log_level)
fh = logging.FileHandler('lp_server_logfile.txt')
fh.setLevel(log_level)
log.addHandler(fh)
log_format = ('%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
log_formatter = logging.Formatter(log_format)
fh.setFormatter(log_formatter)

def main():    
    log.info('#'*40)
    log.info("NEW ENTRY : {}".format(datetime.datetime.now()))
    log.info('#'*40)
    ControlPrompt().cmdloop()



if __name__ == "__main__":
    main()