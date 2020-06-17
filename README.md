# rclip-backends

Back-ends that can be used with the [rclip](https://github.com/noboruma/rclip) CLI tool.

/!\ At the moment, only AWS lambda is supported.

Setup demo:

<a href="https://asciinema.org/a/340551?loop=1&autoplay=1&speed=3"><img src="https://asciinema.org/a/340551.svg" width="400"/></a>

To deploy a new back-end:
- `git clone https://github.com/noboruma/rclip-backends`
- install `serverless`
    - `brew install serverless` or `apt install serverless`
- Choose the backend you want to use
- Follow accoung configuration instructions: [serverless guide](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/)
- `cd` to the chosen back-end
- `sls deploy --verbose`
- Update your `$HOME/.rclip.env` and add your backend `URL=`.
- Done
