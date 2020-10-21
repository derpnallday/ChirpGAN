# ChirpGAN

## Instructions for running programs on server with external notifications

Install `notify-run` package:
```
pip install notify_run
```

Register a channel:
```
notify-run register
```

Send notifications:
```
from notify_run import Notify
notify = Notify()
notify.send('MESSAGE CONTENT')
```
