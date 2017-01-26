(function(){
  "use strict";
  /* global module */
  module.exports = function(grunt) {
    grunt.initConfig({
      eslint: {
        options: {
          configFile: '.eslintrc.js'
        },
        target: ['Gruntfile.js', 'js/*.js']
      },
      requirejs: {
        compile: {
          options: {
            baseUrl: ".",
            mainConfigFile: "js/main.js",
            name: "js/main",
            include: ['bower_components/almond/almond.js'],
            out: "minified.js"
          }
        }
      },
      asset_version_json: {
        assets: {
          options: {
            algorithm: 'sha1',
            length: 8,
            format: false,
            rename: true
          },
          src: './minified.js',
          dest: './assets.json'
        }
      },
      watch: {
        files: ['<%= eslint.files %>'],
        tasks: ['eslint', 'requirejs']
      }
    });

    grunt.loadNpmTasks('grunt-eslint');
    grunt.loadNpmTasks('grunt-contrib-requirejs');
    grunt.loadNpmTasks('grunt-asset-version-json');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('default', ['eslint', 'requirejs', 'asset_version_json']);
  };
})();
