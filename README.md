# Python stratum server
### Simple implementation of stratum server

This is a ***Bitcoin stratum mining pool*** server.</br>
who explain and communicate between a miner and a stratum server. </br>
Server tested in ***main-net*** and ***reg-test*** using  ***[wildrig-multi](https://github.com/andru-kun/wildrig-multi)*** and ***[cpuminer-opt](https://github.com/JayDDee/cpuminer-opt)***.</br>
#### Notice: block submitting method just tested in reg-test (if I could do that in main net, I will leave git forever :stuck_out_tongue_winking_eye: )

### Valid method list:
- **mining.subscribe:**
  + Request body example:
  ````json
  {"id": 1, "method": "mining.subscribe", "params": ["WildRig/0.40.8L"]}
  ```` 
  id = int, request number </br>
  method = str, "mining.subscribe" </br>
  params = list, contain good information about miner </br>
  </br> 
  + Response body example:
  ````json
  {"id": 1, "result": [[["mining.set_difficulty", 32]], "0BFCC3F18A1605AE", 8], "error": null}
  ````
  id = int, response number </br>
  result = list, [[set start worker difficulty], extraNonce1, len of extraNonce2] </br>
  error = bool, is there any error </br>
  </br> 
- **mining.authorize:**
  + Request body example:
  ````json
  {"id": 2, "method": "mining.authorize", "params": ["bc1q05205nxlhgwv33gnd5salpp449m2k9ye8dqg72", ""]}
  ````
  id = int, request number </br>
  method = str, "mining.authorize" </br>
  params = list, [worker address as Username, worker password] </br>
  </br> 
  + Response body example:
  ````json
  {"id": 2, "result": true, "error": null}
  ````
  id = int, response number </br>
  result = bool, is everything okay </br>
  error = bool, is there any error </br>
  </br> 
- **mining.extranonce_subscribe**:
  + Request body example:
  ````json
  {"id": 3, "method": "mining.extranonce.subscribe", "params": []}
  ```` 
  id = int, request number </br>
  method = str, "mining.extranonce.subscribe" </br>
  params = list, it is empty </br>
  </br>
  - Response body example:
  ````json
  {"id": 3, "result": false, "error": null}
  ````
  id = int, response number </br>
  result = bool, if not support False </br>
  error = bool, is there any error </br>
  </br>
- **mining.set_difficulty:**
  + Response body example:
  ````json
  {"id": 4, "method": "mining.set_difficulty", "params": [16.0]}
  ````
  id = int, response number </br>
  method = str, "mining.set_difficulty" </br>
  params = list, worker difficulty as a float number </br>
  </br>
- **mining.notify:**
  + Response body example:
  ````json
  {"id": 2, "method": "mining.notify", "params": ["6742d1ed000d4d29", "c35fe4e2df7c7866d06a8f94b7892106fd7eeb390002a37a0000000000000000", "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff2603294d0d21746f6b696d617940676d61696c2e636f6d", "ffffffff027a88d412000000001600147d14fa4cdfba1cc8c5136d21df8435a976ab14990000000000000000266a24aa21a9ed20cf115aea7d5949653d2935e80d4703829e59539a40e9ede927db49509614dc00000000", ["f640a577fb4ee6989fd7f239beb0e1ca7f21776f9c70dcce929162597f93b10b", "48d0d07032f9bd8d662874927847040d478a0054de0e6923e8a09cf131702ff1", "96ed6a2663ce74bb8a9579eb778eb39c9c2f307daf6a287cc4f0249d6f1222df", "2a90d63ae86657e5d3ee9c9392a8255770a6b2b1563ef8728077b8dc60153a3b", "7e025ab05dd225c9ff43624b3901333558168a9166947448ff35222245befed8", "047a0e4600fbe0d5316a3123fccc7670b68dfe75c7051d3ba74a0e5f87a0bf5a", "bc04c1e8c1ade0ae389cb6887674723398cf4fdde56137e2fe910ab0fcd8776d", "315465f9a46ca9b37ea19692c965fc6277659582cb024ed26710095ee8c1875e", "f7ae16529703835e9170f8d918bd730c720192863b7e37c94b3abd8ca1a1cb18", "4b41fd87dd0182284d76e9a22ba21757a98369e49ee26afc327e8cd3782ab1d6", "b62b23864e8223a37eedab981985df292489333b82675f2317b9b22b84ff8148", "f35ddcb02e7e55d8cddf4d89cf09767a6cc5062c71869ab37f47cb03b63ae715"], "20000000", "1702c070", "6742d1ed", true]}
  ````
  id = int, response number </br>
  method = str, "mining.notify" </br>
  params = list, </br>
  [ </br>
  *hex string job ID*,  </br>
  *hex string previous block hash*, </br>
  *hex string coinBase1*, </br>
  *hex string coinBase2*, </br>
  *list merkle branch*, </br>
  *hex string version*, </br>
  *hex string bits*, </br>
  *hex string time*, </br>
  *bool does worker should forget previous job* </br>
  ]</br>
  ***notice:***</br>
  *The previous block hash* is in [crazy format](https://stackoverflow.com/questions/66412968/hash-of-previous-block-from-stratum-protocol) by changing to a little-endian, each 4-Byte separate. </br>
  *Merkle branch* is not all transaction IDs in block. It is a pre-calculated all transaction ID's hashes.
  </br>
- **mining.submit:**
  + Request body example:
  ````json
  {"method": "mining.submit", "params": ["bc1q05205nxlhgwv33gnd5salpp449m2k9ye8dqg72", "6742d2e1000d4d29", "0000000000000000", "6742d2e1", "bfdc580e"], "id":4}
  ```` 
  method = str, "mining.submit" </br>
  params = list, </br>
  [ </br>
  *hex string worker address as name*,  </br>
  *hex string job ID*, </br>
  *hex string extraNonce2*, </br>
  *hex string time*, </br>
  ]</br>
  id = int, request number </br>
  </br>
  + Response body example:
  ````json
  {"id": 4, "result": false, "error": [23, "Low difficulty share.", null]}
  ````
  id = int, response number </br>
  result = str or bool, mining result </br>
  params = list, error code or None </br>
  </br>
  

### usage:
- At the first step, you should run [Bitcoin core](https://bitcoin.org/en/full-node) software on your machine.
- Edit [bitcoin.config](https://bitcoin.stackexchange.com/questions/11190/where-is-the-configuration-file-of-bitcoin-qt-kept) and set valid username and password for RPC connections.
- Clone this source:
````shell
  git clone https://github.com/tokimay/python_stratum_server 
  ````
- Edit the ***setting.ini*** file (you cloned it in the previous step) and set the bitcoin.config section the same as your bitcoin.config file.
  + rpcuser=YOUR_RPC_USER
  + rpcpassword=YOUR_RPC_PASSWORD
  + host=WHERE_THAT_BITCOIN_CORE_IS_RUNNING
  + port=BITCOIN_CORE_PORT
  + start_difficulty=should be a float number multiple of 2 </br>
  It will tell the miner how to start its job. </br>
  This is completely [different from network difficulty](https://bitcointalk.org/index.php?topic=5474651.0). In a word, just a way to ensure that workers are active and a method for paying rewards to them. </br>
  + btc_address=BTC_WALLET_ADDRESS for receive reward
- At the end, just run: 
````shell
stratumServer.py
  ````