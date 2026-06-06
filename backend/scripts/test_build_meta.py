import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.services.enrich import build_meta
text = "To do this, it compares the network part of the destination address with the network part of the address of each of its network interfaces. (Hosts normally have only one interface, while routers normally have two or more, since they are typically connected to two or more networks.) If a match occurs, then that means that the destination lies on the same physical network as the interface, and the packet can be directly delivered over that network that has a reasonable chance of getting the packet closer to its destination. If there is no match, then the node is not connected to the same physical network as the destination node, then it needs to send the packet to a router."
meta = build_meta({"raw_text": text, "subject": "computer_science", "grade_level": "high-school", "bloom_level": "understand"}, "dyslexia_audio")
print(meta)
print('simulator type:', type(meta.get('simulator')))
