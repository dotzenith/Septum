<h2 align="center"> ━━━━━━  ❖  ━━━━━━ </h2>

### ❖ Information

Septum is a free API that aims to augment [Septa's Public API](https://www3.septa.org/) with useful endpoints that it lacks.

---

### ❖ Usage

The Base URL is:
```
https://septum.jawn.website/api
```

Please see the [docs](https://septum.jawn.website/) for usage of the various endpoints

---

### ❖ Rate Limiting

Septum currently allows 5 requests per minute from a given IP address. In case you desire more, feel free to take a look at the [Self Hosting](#Self-Hosting) section.

---

### ❖ Self Hosting

Septum is relatively easy to self-host. The only requirements are [Docker](https://www.docker.com/), [Git](https://git-scm.com/) and pretty much any webserver, for example: [nginx](https://www.nginx.com/)

#### ❖ Clone repo and cd into it

```
git clone https://github.com/dotzenith/Septum.git
cd Septum
```

<b></b>

#### ❖ Build the image and run the container

```
docker compose up --build -d
```

#### ❖ Set up a reverse proxy

After the step above, set up a reverse proxy using a webserver of your choice and enjoy your very own Septum API :)

---

### ❖ What's New?

0.2.8 - Fix Schedules again

---

<div align="center">

   <img src="https://img.shields.io/static/v1.svg?label=License&message=MIT&color=F5E0DC&labelColor=302D41&style=for-the-badge">

</div>
