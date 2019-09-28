import logging

logger = logging.getLogger(__name__)

def safe_get_logs(event, from_block, to_block):
    try:
        return event(fromBlock=from_block, toBlock=to_block)
    except ValueError as e:
        if "10000 results" in str(e) and from_block != to_block:
            pass
        else:
            raise e
    
    pivot = int((int(to_block) - int(from_block)) / 2 + int(from_block))
    logger.debug("Split getLogs {}/{} into -> {}/{} and {}/{}".format(from_block, to_block, from_block, pivot, pivot, to_block))
    section_a = safe_get_logs(
        event,
        from_block,
        pivot
    )
    section_b = safe_get_logs(
        event,
        pivot,
        to_block
    )

    return section_a + section_b
        
