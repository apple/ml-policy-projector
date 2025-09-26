# 📽️ Policy Projector: Map Visualization Web App

To run Policy Projector with demo data, first run the notebooks in `../notebooks` to download and process the sample dataset.

## Development guide
Start the back-end Flask server:
1. `cd backend`
2. `python run server.py`
3. Open your web browser to `http://localhost:9001/datasets` to confirm the server is running
4. The default port number in debug mode is 9001 and can be edited at the end of `server.py`. For localhost, make sure that the localhost port your server opens in matches the port number in `frontend/src/lib/api.ts` so that the front-end app knows where to call the server.

Next start the front-end app:

1. `cd frontend`
2. `npm i`
3. `npm run dev` then open the provided localhost link in a web browser

### File structure

This app combines several main elements:

1. [Python] backend Flask server
2. [Svelte](https://svelte.dev/) frontend components
3. [Vite](https://vitejs.dev/) setup to build the frontend components

Summary of some of the main files/directories and their purposes:

- `data/` This is the folder for your datasets
- `backend/` The Flask server api
- `frontend/viewer-app`
  - `src/lib`
    - `components\` These are Svelte _template_ reusable components. They should not contain app-specific data.
    - `embeddingMap\` This contains all Svelte components related to the embedding map view
    - `mosaic\` This contains all the DuckDB and Mosaic hookups as well as SQL processing
    - `views\` These are all our app-specific views components. These _do_ contain app-specific data.
    - `api.ts` This is the client side of our API to connect with the Flask server
    - `store.ts` All state writeable stores
    - `types.ts` All app custom types, interfaces, and enums
    - `constants.ts` All app-wide contstant variables, such as SQL table names
  - `src/routes` This is a single-page app (for now), so there is only 1 page under routes
