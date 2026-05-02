import logging

def setup_logger():
    """
    Sistemin tüm modülleri için standartlaştırılmış 
    profesyonel loglama sistemini kurar.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger("AresQuant")
