require.config({
  paths: {
    "jquery": "lib/jquery-2.1.1.min"
  }
});

require(["jquery", "events"], function(jquery, events) {
    console.log("hello world");
});
