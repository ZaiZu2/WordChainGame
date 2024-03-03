# WordChainGame - compete with other players to build the longest word chain

In the Word Chain Game, players take turns adding a word to a growing chain, with each new word starting with the last letter of the previous one. The objective is to build the longest chain without repeating words, and the player who successfully contributes the longest word chain wins the game.
Be advised that this is an ongoing project (started in January).

### ***Features***
  - [x] Play without the necessity to create the account - a UUID can be used to access your account
  - [x] Create and join game rooms - no matter if you play with your friends or alone
  - [x] Communicate with other players in a lobby and room chats.
  - [ ] Play a game
  - [ ] Check the leaderboards and your game history
  - [ ] Deploy using Nginx & Uvicorn

### ***Tech Stack***
  - Frontend – Typescript, React, Boostrap/Bootstrap-React
  - Backend – Fastapi, Pydantic, Websockets, SQLAlchemy, PostgreSQL

### ***Backend***
#### 1. Websockets
Websockets are used to facilitate real-time updates - transporting chat messages, updating available rooms but also synchronizing room and game states across all clients.
#### 2. API
For singular requests and switching client state, normal requests are utilized.
#### 3. Asynchronous web server
All endpoints and functionalities are implement as asynchronous.
#### 4. Database
Application utilizes SQLAlchemy with a PostgreSQL database to persist players, rooms, but also full history of each game. 
#### 5. Validation
Virtually all inputs and outputs are modeled and validated using Pydantic. 

### ***Frontend***
#### 1. Typescript & Javascript
Initially written in JavaScript, the frontend code typing is gradually introduced, with plans to transition fully to TypeScript in the near future.
#### 2. Finite state machine
The frontend is constructed following the finite state machine paradigm and leverages the XState library.
#### 3. React & Bootstrap
React and boostrap are used to provide interactiveness and styling.

### ***Disclaimer***
This application is purely educational endeavor. It's general concept guided me on my learning path, allowing me to recognize various issues and the tools necessary to deal with them.
