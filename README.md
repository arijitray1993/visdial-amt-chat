## VisDial AMT Chat

Source for the two-person chat interface that is planned to be used to collect a Visual 20 Questions oriented dataset on Amazon Mechanical Turk.
A demo is available [here][12] (does not appear to work outside of AMT Sandbox).

![VisDial AMT Interface][11]

### How things work

The real-time chat interface is built using Node.js and Socket.io. We use Redis to maintain a pool of images for live HITs and all data finally resides in a MySQL database.

A database table stores images from the COCO dataset and all object labeled in the dataset. A batch of images from this table are then pushed to a Redis list for launching HITs. The web server corresponding to the chat interface pairs two AMT workers, assigns them roles (questioner or answerer) and shows corresponding interface, picks an image from the Redis list to collect data on, pulls a pool of images with one object in common for the questioner, and saves their conversation in the database, also marking that image as 'complete' once the HIT is done. This happens in parallel so workers aren't left waiting, and the server ensures workers have unique ids. Disconnects are handled gracefully — remaining worker is asked to continue asking questions or providing facts (captions) up to 10 messages. Once the HITs are complete, scripts in `mturk_scripts/approve` can be used to review, approve, reject HITs and pay workers.

### Node.js

Pops images from the Redis list, retrieves relevant data from the MySQL tables, renders the chat interface and pairs workers on AMT, saves submitted data to MySQL tables

* Install [MySQL][9], [Redis][8], [Node][7]
* Install dependencies using `npm install` (from the `nodejs` folder)
* Copy over `example.config.js` to `config.js`, and set MySQL and Redis credentials
* Create a symbolic link from `static/dataset` to `/path/to/mscoco/images/`
* Update app path (from vhost) in `index.html` line 290
* Running `node index.js` should now serve the interface at 127.0.0.1:5000

### MTurk Scripts

Scripts to set up MySQL database, populate Redis list, and approve/reject HITs

* Copy over `example.config.json` to `config.json`, and set MySQL credentials. `from_timestamp` is unix timestamp before launching a batch of HITs
* `createDatabase.py` and `fillDatabase.py` create MySQL tables, populate it with COCO images and objects and generate the Redis list for a batch of HITs
* `createHits.py` launches HITs on AMT

#### Approving/Rejecting HITs (`mturk_scripts/approve`)

* Copy over `example.config.json` to `config.json`, and set MySQL credentials
* Copy over `example.constants.py` to `constants.py`, and set AMT credentials
* `reviewHits.py` gets completed HITs and saves them to `amthitsQues.csv` and `amthitsAns.csv` for review
* Once HITs have been reviewed in the CSV files (by changing 'notApprove' to 'reviewReject' or 'approve'), run `approveHits.py` to mark approved HITs for payment and `reviewRejectedHits.py`, `rejectHits.py` to reject HITs, and finally `payWorkers.py` to process payments

### Contributors

* [Chris Dusold][13]
* [Arijit Ray][16]

### Acknowledgements

Parts of this code (MTurk scripts) are adapted from [@jcjohnson][5]'s [simple-amt][6] project, most of it was adapted from [visdial-amt-chat][15] by [Harsh Agrawal][2], [Khushi Gupta][3], and [Abhishek Das][4] (abhshkdz@vt.edu) whose dataset can be accessed [here][10] and has a paper [here][1].

### License

BSD

[1]: https://arxiv.org/abs/1611.08669
[2]: https://github.com/dexter1691
[3]: http://www.ri.cmu.edu/person.html?person_id=4483
[4]: https://github.com/abhshkdz
[5]: https://github.com/jcjohnson
[6]: https://github.com/jcjohnson/simple-amt
[7]: https://nodejs.org/en/download/
[8]: https://redis.io/
[9]: https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-14-04
[10]: http://visualdialog.org/
[11]: http://imgur.com/y3OMHgq.jpg
[12]: https://workersandbox.mturk.com/mturk/preview?groupId=34VKX0JC68S4225Q5MX0XFLZ8E1RB2
[13]: https://www.chrisdusold.com/
[14]: https://github.com/arijitray1993/visdial-amt-chat
[15]: https://github.com/batra-mlp-lab/visdial-amt-chat
[16]: https://computing.ece.vt.edu/~ray93/
