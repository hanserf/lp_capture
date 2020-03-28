from server.include.usb_collector import USBCollector
import server.include.config as config




#This will put recorded buffer into the tcp server and maintain flow control


    # -------------------------------------------------------------------------------------------------------------------
    #   Create A Process for recording data
    # -------------------------------------------------------------------------------------------------------------------
    rec_queue = queue.Queue()
    recording_process = USBCollector(queue=rec_queue, packet_size=config.packet_size, parser=parser,
                                                   args=args, rec_folder=default_savedir)
    recording_process.daemon = True
    recording_process.start()
    print("Recording Process started")
