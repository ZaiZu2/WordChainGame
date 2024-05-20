# WordChainGame - compete with other players to build the longest word chain

In the Word Chain Game, players take turns adding a word to a growing chain, with each new word starting with the last letter of the previous one. The objective is to build the longest chain without repeating words, and the player who successfully contributes the longest word chain wins the game.

### ***Features***
  - [x] Play without the necessity to create the account - a UUID can be used to access your account
  - [x] Create and join game rooms
  - [x] Close and open a room to avoid unexpected guests
  - [x] Communicate with other players using lobby and room chats.
  - [x] Define game type (well, for now just one) and it's game parameters
  - [x] Kick troublesome players from your room
  - [x] Play a game
  - [X] Go over the game progress after it finishes
  - [x] Run a recurring job, periodically cleaning abandoned room from the lobby
  - [ ] Introduce mute/ownership buttons
  - [ ] Check the leaderboards and your game history
  - [ ] Deploy fully containerized on AWS using Nginx & Uvicorn
  - [ ] Implement as a distributed system, with 2 independent game servers sharing transient state in Redis

### ***Tech Stack***
  - Frontend – Typescript, React, Boostrap/Bootstrap-React
  - Backend – Fastapi, Pydantic, Websockets, SQLAlchemy, PostgreSQL

### ***Backend***
#### 1. Websockets
Websockets are used for broadcasting various events to all affected clients - this includes:
- propagating chat messages
- updating available rooms and their statuses in the lobby
- synchronizing player/room state and settings for all players in a given room
- synchronizing all player with the progress during the game (server-authoritative game)
- and other...
#### 2. API
Actions sent by a client and those which are 'singular' by design, utilize HTTP requests.
#### 3. Asynchronous web server
The webserver is built with FastAPI and features a fully asynchronous code.
#### 4. Persistance
Application stores transient, game-related state in memory - meaning that currently open rooms, active games and player sessions are not persisted. Nonetheless, the history of chat messages, past games (alongside all data to recreate their progress) and players are persisted using SQLAlchemy with a PostgreSQL database.
#### 5. Validation
Virtually all inputs and outputs are modeled and validated using Pydantic.

### ***Frontend***
#### 1. Typescript & Javascript
Initially written in JavaScript, the frontend code typing is gradually introduced, with plans to transition fully to TypeScript in the near future.
#### 2. React & Bootstrap
React and boostrap are used to provide interactiveness and styling.

### ***Disclaimer***
This application is purely educational endeavor. It's general concept guided me on my learning path, allowing me to recognize various issues and the tools necessary to deal with them. Be advised that this is an ongoing project (started in January).
