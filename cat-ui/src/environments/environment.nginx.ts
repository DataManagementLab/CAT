// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  apiUrl: 'http://tcb.local.de/api/v1',
  socketioUrl: 'http://tcb.local.de',
  jwtPassphrase: 'passphrase',
  dbHost: 'localhost',
  dbPort: 5432,
  dbUsername: 'tcb',
  dbPassword: 'tcb',
  dbName: 'tcb',
  dbSchema: 'movie_theatre',
  jwtOn: false
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.
