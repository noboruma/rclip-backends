addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

/**
 * @param {Request} request
 */
async function handleRequest(request) {
    const { greet, bye } = wasm_bindgen;
    var path = get_path(request)
    await wasm_bindgen(wasm)
    return dispatch(path, greet, bye);
}

function get_path(request) {
    var path = request.url.split('/')[3];
    path = path.split('?')[0];
    return path;
}

function dispatch(path, greet, bye) {
    switch (path) {
        case "hello":
            greeting = greet();
            return new Response(greeting, {status: 200});
        default:
            bying = bye();
            return new Response(bying, {status: 200});
    }
}
