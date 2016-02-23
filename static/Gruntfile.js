module.exports = function(grunt){
  grunt.initConfig({
    jshint: {
      files: ['Gruntfile.js', 'js/*.js']
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
    watch: {
      files: ['<%= jshint.files %>'],
      tasks: ['jshint', 'requirejs']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-requirejs');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask('default', ['jshint', 'requirejs']);
};
