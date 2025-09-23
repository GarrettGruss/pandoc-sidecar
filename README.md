# Pandoc-Sidecar

This app is a exposes the pandoc/extra engine through a restful interface for use within a k8s cluster. A fastapi client runs as a sidecar to expose the pandoc/extra functionality via http.

## Resources

- [multiple file uploads](https://fastapi.tiangolo.com/tutorial/request-files/#multiple-file-uploads)

## Structure

This app will be composed of a fastapi client and a pandoc/extra image running in seperate containers, but on the same deployment. They will be mounted to the same file store and will communicate via stdio.