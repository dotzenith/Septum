<h2 align="center"> ━━━━━━  ❖  ━━━━━━ </h2>

<!-- BADGES -->
<div align="center">
   <p></p>

   <img src="https://img.shields.io/github/stars/dotzenith/TheSeptaAPI?color=F8BD96&labelColor=302D41&style=for-the-badge">

   <img src="https://img.shields.io/github/forks/dotzenith/TheSeptaAPI?color=DDB6F2&labelColor=302D41&style=for-the-badge">

   <img src="https://img.shields.io/github/actions/workflow/status/dotzenith/TheSeptaAPI/deploy.yml?branch=main&color=89b4fa&labelColor=302D41&style=for-the-badge&label=Deployment"/>

   <img src="https://img.shields.io/github/actions/workflow/status/dotzenith/TheSeptaAPI/test.yml?branch=main&color=ABE9B3&labelColor=302D41&style=for-the-badge&label=Tests"/>
   <br>
</div>

<p/>

---

### ❖ Information

TheSeptaAPI is a free API that aims to augment [Septa's Public API](https://www3.septa.org/) with useful endpoints that it lacks.

---

### ❖ Usage

The Base URL is:
```
https://septa.jawn.website/api/
```

Please see the [docs](https://septa.jawn.website/) for usage of the various endpoints

---

### ❖ Rate Limiting

TheSeptaAPI currently allows 5 requests per minute from a given IP address. In case you desire more, feel free to take a look at the [Self Hosting](#Self-Hosting) section.

---

### ❖ Self Hosting

TheSeptaAPI is relatively easy to self-host. The only requirements are [Docker](https://www.docker.com/), [Git](https://git-scm.com/) and pretty much any webserver, for example: [nginx](https://www.nginx.com/)

#### ❖ Clone repo and cd into it

```
$ git clone https://github.com/dotzenith/TheSeptaAPI.git
$ cd TheSeptaAPI
```

<b></b>

#### ❖ Build docker image

```
$ docker build -t theseptaapi:latest .
```

#### ❖ Run the container

```
$ docker run -p 8000:8000 -d --name septa theseptaapi:latest
```

#### ❖ Set up a reverse proxy

After the step above, set up a reverse proxy using a webserver of your choice and enjoy your very own TheSeptaAPI :)

---

### ❖ What's New?

0.1.0 - Initial Release

---

<div align="center">

   <img src="https://img.shields.io/static/v1.svg?label=License&message=MIT&color=F5E0DC&labelColor=302D41&style=for-the-badge">

</div>
