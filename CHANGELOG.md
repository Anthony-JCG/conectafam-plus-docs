# Changelog

## [4.0.0](https://github.com/Anthony-JCG/Platform/compare/v3.2.0...v4.0.0) (2026-08-26)


### ⚠ BREAKING CHANGES

* **user_levels:** drop dead leader pro copy flow

### Code Refactoring

* **user_levels:** drop dead leader pro copy flow ([cfd562c](https://github.com/Anthony-JCG/Platform/commit/cfd562c4c9bb8e9bf7f2c2b8b3ec7cd98071dbfa))


### Documentation

* fix docs index link to root readme ([a35a9aa](https://github.com/Anthony-JCG/Platform/commit/a35a9aaf34a4add9843d872aff4b09d4af2f00b3))
* translate docs/ to english and unify conventions ([8baf935](https://github.com/Anthony-JCG/Platform/commit/8baf9351cdc3d26436764db42df37c413161340e))
* unify project documentation and remove dead copy flow ([d99c9e2](https://github.com/Anthony-JCG/Platform/commit/d99c9e2a957941e09a492ad67ef173dff8d07063))

## [3.2.0](https://github.com/Anthony-JCG/Platform/compare/v3.1.0...v3.2.0) (2026-08-25)


### Features

* **landing:** add share-with-team switch for leaders ([#256](https://github.com/Anthony-JCG/Platform/issues/256)) ([4e5221d](https://github.com/Anthony-JCG/Platform/commit/4e5221dc1bb55cff211da6ffafff5bfb794a0492))

## [3.1.0](https://github.com/Anthony-JCG/Platform/compare/v3.0.1...v3.1.0) (2026-08-25)


### Features

* **admin:** add admin interface for general data model ([72ce569](https://github.com/Anthony-JCG/Platform/commit/72ce5695be30e945bf40b28679e0871308fe06a5))
* **main:** add general data model and community link ([b04cae2](https://github.com/Anthony-JCG/Platform/commit/b04cae29c9c596bb28c512bd9ccc33e27747f613))
* **main:** add whatsapp community link to sponsor card ([2a7d094](https://github.com/Anthony-JCG/Platform/commit/2a7d09417b385eb2f93b21261516b9afaa27b691))
* **models:** add general data model for website management ([52445ef](https://github.com/Anthony-JCG/Platform/commit/52445ef53cbdb45d5490d3317877c26ad97a991c))


### Bug Fixes

* **models:** remove unused main page content models ([7be06a7](https://github.com/Anthony-JCG/Platform/commit/7be06a7c272fecb8cc081f39ce14a912562f1682))


### Code Refactoring

* **admin:** simplify general data admin interface ([732adec](https://github.com/Anthony-JCG/Platform/commit/732adec9bef864db57e9b569cb82ddf9eafa4a2c))
* **models:** remove unused import from main models ([efff4e1](https://github.com/Anthony-JCG/Platform/commit/efff4e11d75c7204f2ee786c4054f8203f01139c))

## [3.0.1](https://github.com/Anthony-JCG/Platform/compare/v3.0.0...v3.0.1) (2026-08-24)


### Bug Fixes

* **boards:** allow basic collaborators to edit shared boards ([e26e7e4](https://github.com/Anthony-JCG/Platform/commit/e26e7e451464a7953de20a812d5d87e711f8bc8f))
* **boards:** let leaders share boards with their downline ([0fe6dcc](https://github.com/Anthony-JCG/Platform/commit/0fe6dcc21fb9503d658fa73aa1c7b9cfa419b8a1))
* **core:** stop copy-offer fanout on object creation ([aa78a32](https://github.com/Anthony-JCG/Platform/commit/aa78a322d2aee1181be07fee6b9889b412b110b4))
* **landing:** enforce pro limit and blank-create UX at cap ([cc47405](https://github.com/Anthony-JCG/Platform/commit/cc474050d887a96c7b8d9882e993b9032a1adf8e))
* **main:** require pro plan for incentive favorites ([c753c0f](https://github.com/Anthony-JCG/Platform/commit/c753c0f3e7bc43f49378a629c29ab16119d2541f))
* **training:** restrict formation save endpoints to leaders ([10ceffd](https://github.com/Anthony-JCG/Platform/commit/10ceffde281c7e2a56abf0debefd8e3ce8459bb3))
* **user_levels:** audit and align hierarchy permissions ([9364d0f](https://github.com/Anthony-JCG/Platform/commit/9364d0f47246a5a7b7c6c50d3d55fa02e5ac0e0a))
* **user_levels:** cut downline and visibility at leader_pro ([8040a91](https://github.com/Anthony-JCG/Platform/commit/8040a917ea85e6a90607defe5a0c27f2c149cd7a))


### Documentation

* align boards and landing permission docs ([038d7bc](https://github.com/Anthony-JCG/Platform/commit/038d7bca1bbca5b82c4993746d16dc048735e4d5))

## [3.0.0](https://github.com/Anthony-JCG/Platform/compare/v2.9.0...v3.0.0) (2026-08-21)


### ⚠ BREAKING CHANGES

* **landing:** hide shared wa and remove unused fields

### Features

* **landing:** add pretty urls and unlimited byron create ([56b6b5e](https://github.com/Anthony-JCG/Platform/commit/56b6b5eb7f66e7b21a063007008964b56f5d12f9))
* **pro-components:** add app download buttons for mobile users ([0768b87](https://github.com/Anthony-JCG/Platform/commit/0768b87e3ba4c187b60f2e22c84cbf7b692651d7))
* **training:** let byron edit and align team progress ([36e4c74](https://github.com/Anthony-JCG/Platform/commit/36e4c74226352359593515fcff02e457ec1fa74a))


### Bug Fixes

* **landing, boards:** update byron limits & boards url ([151dd68](https://github.com/Anthony-JCG/Platform/commit/151dd68a6ddf7aafa31b557d93ac2c2755f6bff9))
* **landing:** hide shared wa and remove unused fields ([4e305be](https://github.com/Anthony-JCG/Platform/commit/4e305be946f25e1fd55105691d35006cec7243e1))


### Code Refactoring

* **notifications:** remove unused notify_leaders_on_creation function ([d9f0972](https://github.com/Anthony-JCG/Platform/commit/d9f097285bb4453998d27dfb3016d2451272be9c))

## [2.9.0](https://github.com/Anthony-JCG/Platform/compare/v2.8.1...v2.9.0) (2026-08-18)


### Features

* **core:** add short_name attribute to Option class and update shortcuts bar ([4da602a](https://github.com/Anthony-JCG/Platform/commit/4da602a44a5180d3d2653919e99bc5d4080a2a56))
* **core:** add shortcuts bar options to context processor ([7abab7f](https://github.com/Anthony-JCG/Platform/commit/7abab7f5b087c6d222c4549b1a685022db9e1779))
* **main:** add shortcuts bar fixed layout and styles ([6ba7716](https://github.com/Anthony-JCG/Platform/commit/6ba7716e97688e40ab28ab864852ed9527ef25c0))
* **main:** shortcuts bar and navbar search refactor ([d914721](https://github.com/Anthony-JCG/Platform/commit/d9147219f1762b0230ddc3b54ec931464d1bc7ed))


### Bug Fixes

* **core:** silence routine web fcm invalid token errors ([#247](https://github.com/Anthony-JCG/Platform/issues/247)) ([7f5cc64](https://github.com/Anthony-JCG/Platform/commit/7f5cc647f6f60ed6c1c6d6c55ecfc1ee659a77d3))


### Code Refactoring

* **core:** update icon names in context processor ([36826ce](https://github.com/Anthony-JCG/Platform/commit/36826ce8a448262ee4f2616186e974a35dc2dfa4))
* **global_search:** simplify string interpolation in search functions ([a7de55a](https://github.com/Anthony-JCG/Platform/commit/a7de55a5c1a8fcd07a18a680bfaa0b9836e92f44))
* **main:** move global search to navbar ([509569a](https://github.com/Anthony-JCG/Platform/commit/509569a50ac521a3a45ab642683560292b959c9c))
* **navbar:** update mobile search button integration ([a9550fc](https://github.com/Anthony-JCG/Platform/commit/a9550fcead028aaac9e6c3f62557184f0abafd06))
* **notification:** update mobile notification button style and text ([782b024](https://github.com/Anthony-JCG/Platform/commit/782b02486fc0b1c9104cc6aecad005a009c2d15b))

## [2.8.1](https://github.com/Anthony-JCG/Platform/compare/v2.8.0...v2.8.1) (2026-08-15)


### Bug Fixes

* **boards:** viewport layout and drag scroll lock ([#246](https://github.com/Anthony-JCG/Platform/issues/246)) ([dda49fb](https://github.com/Anthony-JCG/Platform/commit/dda49fbb0641dd11c84350cd13c15e7d5b39ae8d))


### Code Refactoring

* **layout:** adopt flex app shell and sticky header ([#244](https://github.com/Anthony-JCG/Platform/issues/244)) ([998d75d](https://github.com/Anthony-JCG/Platform/commit/998d75d48bb805ec6894776865c7e658f5dc5724))

## [2.8.0](https://github.com/Anthony-JCG/Platform/compare/v2.7.3...v2.8.0) (2026-08-13)


### Features

* **legal:** host keyboard privacy policy page ([95ed285](https://github.com/Anthony-JCG/Platform/commit/95ed285a48b2077db5b9f272334ab5c5b3e22661))


### Bug Fixes

* **fcm:** repair push retry and link mate toggles ([1b5cfee](https://github.com/Anthony-JCG/Platform/commit/1b5cfee40b17fd8383327f841bbb020441638818))
* **fcm:** skip empty-sub retry and add gcm sender ([9ac9a5b](https://github.com/Anthony-JCG/Platform/commit/9ac9a5b9dc9f94ecee50e22140582810587ab498))
* **links:** update toggles without save row errors ([2627969](https://github.com/Anthony-JCG/Platform/commit/26279697617a254865d561f6dabde68eb5524f2c))

## [2.7.3](https://github.com/Anthony-JCG/Platform/compare/v2.7.2...v2.7.3) (2026-08-13)


### Bug Fixes

* **fcm:** repair push subscribe and report getToken ([0f12e00](https://github.com/Anthony-JCG/Platform/commit/0f12e006a029de382683604e724edcfcd922022f))
* **manifest:** correct short name in manifest file ([27c4a4a](https://github.com/Anthony-JCG/Platform/commit/27c4a4a8eb1ff0bff33cc81549dfa06522dbc358))


### Code Refactoring

* **fcm:** use vapid key without sanitizing ([6efeef4](https://github.com/Anthony-JCG/Platform/commit/6efeef49aab6e1ec548e2cbc6221ca8ccc953be0))
* **landing:** rename whatsapp button and update labels ([badb027](https://github.com/Anthony-JCG/Platform/commit/badb027a7f02c5648e6e00e940c43851461ee84b))

## [2.7.2](https://github.com/Anthony-JCG/Platform/compare/v2.7.1...v2.7.2) (2026-08-13)


### Bug Fixes

* restore visible web push and table dropdowns ([#238](https://github.com/Anthony-JCG/Platform/issues/238)) ([deceffc](https://github.com/Anthony-JCG/Platform/commit/deceffc1ad88e9727ee01a726d468ff9fc892b3e))

## [2.7.1](https://github.com/Anthony-JCG/Platform/compare/v2.7.0...v2.7.1) (2026-08-12)


### Bug Fixes

* **ops:** avoid tablespace and r2 createbucket errors ([#235](https://github.com/Anthony-JCG/Platform/issues/235)) ([305667f](https://github.com/Anthony-JCG/Platform/commit/305667f09dd60a8f8580c3b511f9d23a48a9f2f7))

## [2.7.0](https://github.com/Anthony-JCG/Platform/compare/v2.6.1...v2.7.0) (2026-08-12)


### Features

* **landing:** natural image ratio and share dropdown fix ([46befea](https://github.com/Anthony-JCG/Platform/commit/46befea438a2745d388f435b580174798b87f669))
* **landing:** show image blocks at natural aspect ratio ([dde2f1f](https://github.com/Anthony-JCG/Platform/commit/dde2f1f3729816341dfae178643b12ae5e85c10d))
* **my-team:** add sponsor card and calendar link field ([2823cac](https://github.com/Anthony-JCG/Platform/commit/2823cac1b74860e72ae24ced14c23c4c7cdb37ce))
* **my-team:** add sponsor card component and style adjustments ([b2a67ab](https://github.com/Anthony-JCG/Platform/commit/b2a67ab99ff61f4b232f7394921ceb1a1b0c4a85))
* **ops:** add daily mysql backups to cloudflare r2 ([#234](https://github.com/Anthony-JCG/Platform/issues/234)) ([b63f269](https://github.com/Anthony-JCG/Platform/commit/b63f26930458e409640bfed5b3d395a5ef374e98))
* **users:** add calendar link field to user model ([7cc14e1](https://github.com/Anthony-JCG/Platform/commit/7cc14e110852b7e3931d88d71619a88194644920))


### Bug Fixes

* **challenge:** restore in-app notification on challenge join ([#229](https://github.com/Anthony-JCG/Platform/issues/229)) ([d721f06](https://github.com/Anthony-JCG/Platform/commit/d721f0695b9ffd16717ee4630b87bdc333a0f0f3))
* **fcm:** surface getToken AbortError diagnostics in Sentry ([#230](https://github.com/Anthony-JCG/Platform/issues/230)) ([e9fc157](https://github.com/Anthony-JCG/Platform/commit/e9fc1572d0d62ad53d68c567d87c5d9117d35167))
* **js:** remove jquery from modals and harden front errors ([#227](https://github.com/Anthony-JCG/Platform/issues/227)) ([2caa82b](https://github.com/Anthony-JCG/Platform/commit/2caa82b355bce3ebfdf3bb91f816b4e0856d747a))
* **landing:** keep share dropdown above card overflow ([8385084](https://github.com/Anthony-JCG/Platform/commit/83850841ca3aba267de1fb6a6533f15d3ce523e8))
* **main:** keep countdown units when timer expires ([6424d26](https://github.com/Anthony-JCG/Platform/commit/6424d26be76b84eb1cf482724c2074b56844d319))
* **training:** cut first steps visibility at byronjr.gio line ([#233](https://github.com/Anthony-JCG/Platform/issues/233)) ([c0e18bd](https://github.com/Anthony-JCG/Platform/commit/c0e18bd0b265df45c747f7d9fd71a0b01ae636d1))

## [2.6.1](https://github.com/Anthony-JCG/Platform/compare/v2.6.0...v2.6.1) (2026-08-11)


### Bug Fixes

* **fcm:** web push observability and env validation ([#225](https://github.com/Anthony-JCG/Platform/issues/225)) ([796b7ed](https://github.com/Anthony-JCG/Platform/commit/796b7edf59ba0db80c2d1bd5c192ae1765066b06))

## [2.6.0](https://github.com/Anthony-JCG/Platform/compare/v2.5.0...v2.6.0) (2026-08-11)


### Features

* **config:** enable cloudflare r2 media storage ([#223](https://github.com/Anthony-JCG/Platform/issues/223)) ([282a2ac](https://github.com/Anthony-JCG/Platform/commit/282a2ac79a9e752209971a61bdcd41e0973e624c))


### Bug Fixes

* **fcm:** sentry jquery guards and transient fcm retries ([#221](https://github.com/Anthony-JCG/Platform/issues/221)) ([4a5048e](https://github.com/Anthony-JCG/Platform/commit/4a5048e861d938c242bc41e2085ff612dd7b487f))

## [2.5.0](https://github.com/Anthony-JCG/Platform/compare/v2.4.4...v2.5.0) (2026-08-11)


### Features

* **landing:** gate blank create UI for non-leaders ([f4a817a](https://github.com/Anthony-JCG/Platform/commit/f4a817af2aada6dcf8a6f8b168fb366b004d87a7))
* **notifications:** migrate web push to firebase fcm ([1743b59](https://github.com/Anthony-JCG/Platform/commit/1743b59826825f25a62d9d932207ed1b4ae72252))


### Bug Fixes

* **challenge:** store start_date via localdate ([8f1f6af](https://github.com/Anthony-JCG/Platform/commit/8f1f6afd0d0b5ef80106f5ba859e1251cdd7cd28))
* **landing:** gate pro create and page break rem ([7b312ba](https://github.com/Anthony-JCG/Platform/commit/7b312ba36e51f650cde7c7965e35d3d5f6287461))
* **landing:** make page_break_rem optional on block save ([e176662](https://github.com/Anthony-JCG/Platform/commit/e17666236ea0a1ceaa84a15fc158f76cfb9dc8e4))
* **landing:** update help text and verbose name for page break rem ([17fc2f1](https://github.com/Anthony-JCG/Platform/commit/17fc2f103e8e1557d8e812bea81762b707e70f80))
* **notifications:** handle fcm errors without invalidarg ([61dabc1](https://github.com/Anthony-JCG/Platform/commit/61dabc124761197102e6e805f28f05d58eff08cf))
* production batch (sentry, fcm, landing, challenge, boards) ([4156cce](https://github.com/Anthony-JCG/Platform/commit/4156cce3def4dad37acb88e186ff5f3f39f6416a))
* **sentry:** resolve six production error issues ([e3bc914](https://github.com/Anthony-JCG/Platform/commit/e3bc9148b35670e820077732bc4ca0507f625a98))


### Performance Improvements

* **boards:** defer search index and skip link http ([39e6ade](https://github.com/Anthony-JCG/Platform/commit/39e6ade162963ed5a6ed75ad1b4c6b861fa2baf3))

## [2.4.4](https://github.com/Anthony-JCG/Platform/compare/v2.4.3...v2.4.4) (2026-08-07)


### Bug Fixes

* improve dev/test context for restricted access ([#215](https://github.com/Anthony-JCG/Platform/issues/215)) ([c44134e](https://github.com/Anthony-JCG/Platform/commit/c44134e61c3b7a3e0bee9b79256b71f0542aa162))
* **landing:** editor import ux and block list previews ([#218](https://github.com/Anthony-JCG/Platform/issues/218)) ([11c90e1](https://github.com/Anthony-JCG/Platform/commit/11c90e1df3a568ccec76460817a030c84b66cba4))


### Code Refactoring

* **boards:** htmx modals, navigation, item form and destination picker ([#217](https://github.com/Anthony-JCG/Platform/issues/217)) ([53866c3](https://github.com/Anthony-JCG/Platform/commit/53866c35222e894215f1bc6d1bd4f6de627225ae))

## [2.4.3](https://github.com/Anthony-JCG/Platform/compare/v2.4.2...v2.4.3) (2026-08-06)


### Bug Fixes

* **boards:** dedupe keyboard sync and add access signals ([#213](https://github.com/Anthony-JCG/Platform/issues/213)) ([e1ad159](https://github.com/Anthony-JCG/Platform/commit/e1ad1595a1efe60808f0c0d1f8090da8b59e2b6d))

## [2.4.2](https://github.com/Anthony-JCG/Platform/compare/v2.4.1...v2.4.2) (2026-08-05)


### Bug Fixes

* **core:** set user root constants per environment ([#211](https://github.com/Anthony-JCG/Platform/issues/211)) ([605535c](https://github.com/Anthony-JCG/Platform/commit/605535c82d8f389f09a2e9a3bcf41073f6fc1853))

## [2.4.1](https://github.com/Anthony-JCG/Platform/compare/v2.4.0...v2.4.1) (2026-08-05)


### Bug Fixes

* **users:** bootstrap multi-account registry for legacy sessions ([#209](https://github.com/Anthony-JCG/Platform/issues/209)) ([d7abfb0](https://github.com/Anthony-JCG/Platform/commit/d7abfb07dacd48aa0c47854b6fd3b88da1f857f4))

## [2.4.0](https://github.com/Anthony-JCG/Platform/compare/v2.3.1...v2.4.0) (2026-08-05)


### Features

* **users:** add multi-account session management ([#206](https://github.com/Anthony-JCG/Platform/issues/206)) ([d7743e3](https://github.com/Anthony-JCG/Platform/commit/d7743e3418b25360b3e56214ff4bb4f11c18313a))
* **users:** migrate system account to Sistema_FAM_Team ([#208](https://github.com/Anthony-JCG/Platform/issues/208)) ([7be8fa4](https://github.com/Anthony-JCG/Platform/commit/7be8fa405129d76a53cd4aad827db30383222d4e))

## [2.3.1](https://github.com/Anthony-JCG/Platform/compare/v2.3.0...v2.3.1) (2026-08-04)


### Bug Fixes

* **pricing:** read billing period from stripe subscription items ([#204](https://github.com/Anthony-JCG/Platform/issues/204)) ([fb16c85](https://github.com/Anthony-JCG/Platform/commit/fb16c850e440b4e9b055be27b996294c29958201))

## [2.3.0](https://github.com/Anthony-JCG/Platform/compare/v2.2.0...v2.3.0) (2026-08-03)


### Features

* **pricing:** add stripe subscription record and caching ([#202](https://github.com/Anthony-JCG/Platform/issues/202)) ([71cb678](https://github.com/Anthony-JCG/Platform/commit/71cb67869464ee95d2e080cd06d16aef053dbbee))

## [2.2.0](https://github.com/Anthony-JCG/Platform/compare/v2.1.0...v2.2.0) (2026-07-30)


### Features

* **landing:** allow board collaborators to edit linked landings ([#199](https://github.com/Anthony-JCG/Platform/issues/199)) ([6a8ae14](https://github.com/Anthony-JCG/Platform/commit/6a8ae1440ae964a7508ea029b8ee7c9e0058189a))

## [2.1.0](https://github.com/Anthony-JCG/Platform/compare/v2.0.3...v2.1.0) (2026-07-29)


### Features

* **core:** add htmx modal form snapshot pattern ([1acc9c6](https://github.com/Anthony-JCG/Platform/commit/1acc9c614cb4a8043a1cd4b1878e2ddb36f0ce01))
* **core:** sentry noise, quill htmx, modal snapshot ([394c63c](https://github.com/Anthony-JCG/Platform/commit/394c63c0bbb2ac165e825f84d36fed001bc9aa91))


### Bug Fixes

* **main:** reinit quill after incentive htmx swap ([f60e73f](https://github.com/Anthony-JCG/Platform/commit/f60e73fecce0fb036055ba8a1a02b2f4c58b2f81))
* **sentry:** ignore instagram iab webkit bridge noise ([c0075b5](https://github.com/Anthony-JCG/Platform/commit/c0075b5150127498fdaeacffdd840319acbf1bd0))

## [2.0.3](https://github.com/Anthony-JCG/Platform/compare/v2.0.2...v2.0.3) (2026-07-29)


### Bug Fixes

* **communication:** allow creating contacts without phone number ([#195](https://github.com/Anthony-JCG/Platform/issues/195)) ([9eb9cb1](https://github.com/Anthony-JCG/Platform/commit/9eb9cb10a3efe551786776affb7c967e56343d06))
* **core:** resolve home static manifest error (PYTHON-DJANGO-1B) ([#193](https://github.com/Anthony-JCG/Platform/issues/193)) ([40e1fb7](https://github.com/Anthony-JCG/Platform/commit/40e1fb7da0d997fce9d5ac1db7c21cda46be3f02))

## [2.0.2](https://github.com/Anthony-JCG/Platform/compare/v2.0.1...v2.0.2) (2026-07-28)


### Code Refactoring

* update-google-token-verificatiom ([#191](https://github.com/Anthony-JCG/Platform/issues/191)) ([f3bf1fb](https://github.com/Anthony-JCG/Platform/commit/f3bf1fbb781d2b4a97bf07dbcdfa068807106752))

## [2.0.1](https://github.com/Anthony-JCG/Platform/compare/v2.0.0...v2.0.1) (2026-07-28)


### Code Refactoring

* **landing:** adopt htmx content editor and list crud ([#188](https://github.com/Anthony-JCG/Platform/issues/188)) ([60e0ce6](https://github.com/Anthony-JCG/Platform/commit/60e0ce686270c2d5dc8d39ebe171ac28917c99eb))
* **users:** unify auth templates and fix reset email ([#190](https://github.com/Anthony-JCG/Platform/issues/190)) ([e7ce393](https://github.com/Anthony-JCG/Platform/commit/e7ce3939d5b2c7064fbb310135a6d952b64cdc4a))

## [2.0.0](https://github.com/Anthony-JCG/Platform/compare/v1.16.1...v2.0.0) (2026-07-27)


### ⚠ BREAKING CHANGES

* Forced major version bump due to domain migration

### Features

* **css:** add design tokens and update brand theme ([#180](https://github.com/Anthony-JCG/Platform/issues/180)) ([33a0190](https://github.com/Anthony-JCG/Platform/commit/33a0190300a460b4ab16bfa9eb0f4da004f27229))
* daily scheduled task reminders at 6am Madrid ([#185](https://github.com/Anthony-JCG/Platform/issues/185)) ([406b006](https://github.com/Anthony-JCG/Platform/commit/406b0069c8d719f03ca4feb28d6108dd02fed99d))


### Bug Fixes

* **docker:** move app image to service level in compose ([#184](https://github.com/Anthony-JCG/Platform/issues/184)) ([d6d6fea](https://github.com/Anthony-JCG/Platform/commit/d6d6fea6e935d11e44caf2fe5596229ff9c60e3a))
* **docker:** sync nginx static from platform-app image ([#183](https://github.com/Anthony-JCG/Platform/issues/183)) ([0505f71](https://github.com/Anthony-JCG/Platform/commit/0505f710cafb69492762013f3f2aefd7a654693b))


### Code Refactoring

* **templates:** update button color classes to remove 'primary' ([#182](https://github.com/Anthony-JCG/Platform/issues/182)) ([f7808c1](https://github.com/Anthony-JCG/Platform/commit/f7808c19c33f0a58f70f2c00a8dfd10c27b081c8))


### Maintenance

* fix release versioning for domain change" -m "BREAKING CHANGE: Forced major version bump due to domain migration ([#187](https://github.com/Anthony-JCG/Platform/issues/187)) ([35b0599](https://github.com/Anthony-JCG/Platform/commit/35b05999ce21af981a28d2c80746d40875072a45))

## [1.16.1](https://github.com/Anthony-JCG/Platform/compare/v1.16.0...v1.16.1) (2026-07-23)


### Code Refactoring

* **main:** adopt htmx on home and my-team pages ([#178](https://github.com/Anthony-JCG/Platform/issues/178)) ([ba8b2a0](https://github.com/Anthony-JCG/Platform/commit/ba8b2a08c7ff07845ff894320d6328a0b123c9d2))

## [1.16.0](https://github.com/Anthony-JCG/Platform/compare/v1.15.0...v1.16.0) (2026-07-22)


### Features

* **core:** add test environment variable to context and template ([#175](https://github.com/Anthony-JCG/Platform/issues/175)) ([a77e909](https://github.com/Anthony-JCG/Platform/commit/a77e9099a4fcd1a7717adad5512c863c5439084f))


### Performance Improvements

* **communication:** optimize contacts load and compress photos ([#177](https://github.com/Anthony-JCG/Platform/issues/177)) ([b07acf8](https://github.com/Anthony-JCG/Platform/commit/b07acf81a46c64a263ef9ecdade4c32f30cb8021))

## [1.15.0](https://github.com/Anthony-JCG/Platform/compare/v1.14.3...v1.15.0) (2026-07-21)


### Features

* **communication:** dry htmx modal lifecycle; fix reopen and loadmore ([65dd7c5](https://github.com/Anthony-JCG/Platform/commit/65dd7c580ba604fd31944c38c82d396f444f3ea8))


### Bug Fixes

* **core:** fix tooltip element null race; add htmx error observability ([2e047db](https://github.com/Anthony-JCG/Platform/commit/2e047db2a839d65aded8a3f8d6c191ebd50e2f49))
* **core:** fix tooltip race, htmx modals, and sw cache ([9cfe1b2](https://github.com/Anthony-JCG/Platform/commit/9cfe1b2f03c928048d4d48f16a967e225d3e4510))
* **core:** remove forced sw update reload; keep skip-waiting ([31dadf3](https://github.com/Anthony-JCG/Platform/commit/31dadf398a7fe5b1a2cedebd76d9522a7abdbf12))


### Performance Improvements

* **core:** cache-first sw strategy for all static assets ([13b7bfe](https://github.com/Anthony-JCG/Platform/commit/13b7bfe77ed4bb8a351298f3cf7d4c83fad88806))

## [1.14.3](https://github.com/Anthony-JCG/Platform/compare/v1.14.2...v1.14.3) (2026-07-21)


### Bug Fixes

* **communication:** htmx modal forms and contact id handling ([#171](https://github.com/Anthony-JCG/Platform/issues/171)) ([905fe6b](https://github.com/Anthony-JCG/Platform/commit/905fe6b3752cdb7affb277675ae094c9e7394bf8))

## [1.14.2](https://github.com/Anthony-JCG/Platform/compare/v1.14.1...v1.14.2) (2026-07-21)


### Code Refactoring

* **communication:** htmx modal flows, extract services, eliminate modal_control ([#169](https://github.com/Anthony-JCG/Platform/issues/169)) ([ae98550](https://github.com/Anthony-JCG/Platform/commit/ae985503cbad32d6fc5a9396ca63f9d2bb21b978))

## [1.14.1](https://github.com/Anthony-JCG/Platform/compare/v1.14.0...v1.14.1) (2026-07-20)


### Code Refactoring

* **main:** extract services and improve page load ([#167](https://github.com/Anthony-JCG/Platform/issues/167)) ([b116e6e](https://github.com/Anthony-JCG/Platform/commit/b116e6e8837aa0493e6b88f29158d3ce9687b835))

## [1.14.0](https://github.com/Anthony-JCG/Platform/compare/v1.13.3...v1.14.0) (2026-07-17)


### Features

* **user_levels:** add configurable restricted access alerts ([#165](https://github.com/Anthony-JCG/Platform/issues/165)) ([f67b048](https://github.com/Anthony-JCG/Platform/commit/f67b048da14a36d8362491a2bd1740f7d2a83a08))

## [1.13.3](https://github.com/Anthony-JCG/Platform/compare/v1.13.2...v1.13.3) (2026-07-13)


### Bug Fixes

* **boards:** fix empty destination select on safari ([#162](https://github.com/Anthony-JCG/Platform/issues/162)) ([7b30356](https://github.com/Anthony-JCG/Platform/commit/7b303565394454c70dd7b373f1acb45b351704f9))
* **main:** block team email and whatsapp for basic users ([#164](https://github.com/Anthony-JCG/Platform/issues/164)) ([83bfe4e](https://github.com/Anthony-JCG/Platform/commit/83bfe4e35c876237528bbe7ab2a6b855079a88d1))
* **ui:** resolve tooltip and contact import sentry errors ([#161](https://github.com/Anthony-JCG/Platform/issues/161)) ([39d67d9](https://github.com/Anthony-JCG/Platform/commit/39d67d968ce0feafbf9436f3311f7ad3a2cac618))

## [1.13.2](https://github.com/Anthony-JCG/Platform/compare/v1.13.1...v1.13.2) (2026-07-11)


### Bug Fixes

* **boards:** raise client upload limit to 25 mb ([#159](https://github.com/Anthony-JCG/Platform/issues/159)) ([3b0bba9](https://github.com/Anthony-JCG/Platform/commit/3b0bba96eec658387921e2b0f0e14bdc7a1d017f))

## [1.13.1](https://github.com/Anthony-JCG/Platform/compare/v1.13.0...v1.13.1) (2026-07-11)


### Bug Fixes

* **boards:** handle mosaic 404 as json not html ([#157](https://github.com/Anthony-JCG/Platform/issues/157)) ([4ac305c](https://github.com/Anthony-JCG/Platform/commit/4ac305cd0c78ea080166e24448c40be410263c9a))

## [1.13.0](https://github.com/Anthony-JCG/Platform/compare/v1.12.9...v1.13.0) (2026-07-11)


### Features

* **challenge:** block personal task create and fix plan limits modal ([#153](https://github.com/Anthony-JCG/Platform/issues/153)) ([8a7bc7b](https://github.com/Anthony-JCG/Platform/commit/8a7bc7b12b0d4e63e57ab4736d304fb85e091c12))
* **communication:** optimize contacts, plan limits and infinite scroll ([#155](https://github.com/Anthony-JCG/Platform/issues/155)) ([0892a21](https://github.com/Anthony-JCG/Platform/commit/0892a21e1cd1609e47d8b4c2bf80479836a7aa87))
* **main:** block team tree and add sponsor register link ([#154](https://github.com/Anthony-JCG/Platform/issues/154)) ([2045002](https://github.com/Anthony-JCG/Platform/commit/2045002ed5dc81f5e5e0f526e13a9d37de03a002))
* **pricing:** enable leader pro checkout, comparison PDF and follow-up catalog ([#156](https://github.com/Anthony-JCG/Platform/issues/156)) ([d6e08c4](https://github.com/Anthony-JCG/Platform/commit/d6e08c43e6f52aa092811150f60896e211a9037a))


### Bug Fixes

* **docker:** add static file handling and synchronization ([#148](https://github.com/Anthony-JCG/Platform/issues/148)) ([bb0613f](https://github.com/Anthony-JCG/Platform/commit/bb0613fa1d4204cd734f5771f7ed5547c0b14a51))
* **docker:** serve static from nginx image build ([#149](https://github.com/Anthony-JCG/Platform/issues/149)) ([9d0f979](https://github.com/Anthony-JCG/Platform/commit/9d0f979525e4e1c19ca5c985e3bb63fcfde94e9c))
* **frontend:** self-host vendor js and fix sw ios ([#144](https://github.com/Anthony-JCG/Platform/issues/144)) ([e4dd99d](https://github.com/Anthony-JCG/Platform/commit/e4dd99d60a223d6c7b395374324297061f9f3a8e))
* **pwa:** harden service worker registration and onboarding script safety ([#150](https://github.com/Anthony-JCG/Platform/issues/150)) ([5b6767c](https://github.com/Anthony-JCG/Platform/commit/5b6767cd44d8ca86cfd49c955f7fb57b51b080ec))
* **training:** remove obsolete free trial end modal copy ([#152](https://github.com/Anthony-JCG/Platform/issues/152)) ([c476d66](https://github.com/Anthony-JCG/Platform/commit/c476d66e519aa6565b532f680ad76d80c81b8755))


### Code Refactoring

* **user_levels:** align permissions with new level rules ([#147](https://github.com/Anthony-JCG/Platform/issues/147)) ([6d086c5](https://github.com/Anthony-JCG/Platform/commit/6d086c5437b30f678b368b2b6c68246df0b19bed))
* **user_levels:** defer excess reconcile to command ([#151](https://github.com/Anthony-JCG/Platform/issues/151)) ([f9339bd](https://github.com/Anthony-JCG/Platform/commit/f9339bde0a0498dfdace204ee5f772be8a8567bf))


### Documentation

* **user_levels:** update README with detailed model descriptions ([#146](https://github.com/Anthony-JCG/Platform/issues/146)) ([a2c8d15](https://github.com/Anthony-JCG/Platform/commit/a2c8d152f5cc3dc8da0c68c5e0cd5c08de1a3acc))

## [1.12.9](https://github.com/Anthony-JCG/Platform/compare/v1.12.8...v1.12.9) (2026-07-08)


### Bug Fixes

* **pwa:** guard notification api on ios ([#142](https://github.com/Anthony-JCG/Platform/issues/142)) ([0a1aa47](https://github.com/Anthony-JCG/Platform/commit/0a1aa47e699cbbbe2f08a9d23743849c55b05611))

## [1.12.8](https://github.com/Anthony-JCG/Platform/compare/v1.12.7...v1.12.8) (2026-07-08)


### Bug Fixes

* **boards:** duplicate csrf retry error ([#141](https://github.com/Anthony-JCG/Platform/issues/141)) ([346dff4](https://github.com/Anthony-JCG/Platform/commit/346dff479dbf46f77efa4dec45098cbc5adf1e6c))
* **main:** pass title_incentive in incentive notify ([#137](https://github.com/Anthony-JCG/Platform/issues/137)) ([41f6dd1](https://github.com/Anthony-JCG/Platform/commit/41f6dd1a70c0b517eae5262b956fabe888adea49))
* **users:** notify sender on refused email recipient ([#140](https://github.com/Anthony-JCG/Platform/issues/140)) ([0779f0a](https://github.com/Anthony-JCG/Platform/commit/0779f0a74c79c4f89983ffec1c126c4f1973bb7e))


### Performance Improvements

* **communication:** prefetch membership status on contacts ([#138](https://github.com/Anthony-JCG/Platform/issues/138)) ([0a6b61e](https://github.com/Anthony-JCG/Platform/commit/0a6b61ec00d0e7ee4349f95fbd17178d253ee94e))

## [1.12.7](https://github.com/Anthony-JCG/Platform/compare/v1.12.6...v1.12.7) (2026-07-02)


### Bug Fixes

* **boards:** send url public in board payload ([#135](https://github.com/Anthony-JCG/Platform/issues/135)) ([ebe2ebd](https://github.com/Anthony-JCG/Platform/commit/ebe2ebd2321cb0008e879f8869caf8833c3952a5))

## [1.12.6](https://github.com/Anthony-JCG/Platform/compare/v1.12.5...v1.12.6) (2026-07-02)


### Bug Fixes

* **settings:** remove unnecesary host ([#134](https://github.com/Anthony-JCG/Platform/issues/134)) ([9e3b0f0](https://github.com/Anthony-JCG/Platform/commit/9e3b0f0594038a06f207c8bcf97fb22a12175794))


### Performance Improvements

* **boards:** adjust image processing quality on save ([#132](https://github.com/Anthony-JCG/Platform/issues/132)) ([6cc2478](https://github.com/Anthony-JCG/Platform/commit/6cc24789644e53573da9b4778983ceb53f427f41))

## [1.12.5](https://github.com/Anthony-JCG/Platform/compare/v1.12.4...v1.12.5) (2026-07-02)


### Bug Fixes

* **boards:** ajax csrf fixes, import reliability and sentry reporting ([#129](https://github.com/Anthony-JCG/Platform/issues/129)) ([ef6adaa](https://github.com/Anthony-JCG/Platform/commit/ef6adaafbd6a0135e4a66e9fdd2b5f0bf779967c))
* **boards:** item viewer edit, share and text clamp ([#125](https://github.com/Anthony-JCG/Platform/issues/125)) ([2be9db8](https://github.com/Anthony-JCG/Platform/commit/2be9db8773634c21b825dd6ab36df9ac790c2c9c))
* **boards:** keyboard sync on reorder and board page updates ([#131](https://github.com/Anthony-JCG/Platform/issues/131)) ([65d9d9a](https://github.com/Anthony-JCG/Platform/commit/65d9d9a8034151a3267a0f1b693af6ff71f7036f))
* **landing:** remove whatsapp cta and fix board page video saves ([#128](https://github.com/Anthony-JCG/Platform/issues/128)) ([d536136](https://github.com/Anthony-JCG/Platform/commit/d536136e368d9fca8b7f785c63add2d1147cc417))
* optimice sortable items ([#123](https://github.com/Anthony-JCG/Platform/issues/123)) ([3ddcc55](https://github.com/Anthony-JCG/Platform/commit/3ddcc556c5933e45cf338a28ecff3d5ab89c7e11))


### Code Refactoring

* **boards:** split boards css into partial modules ([#130](https://github.com/Anthony-JCG/Platform/issues/130)) ([ea68c99](https://github.com/Anthony-JCG/Platform/commit/ea68c9968dee69f3e345e131108965c43f0455f6))

## [1.12.4](https://github.com/Anthony-JCG/Platform/compare/v1.12.3...v1.12.4) (2026-06-28)


### Bug Fixes

* **boards:** handle mosaic preview permission errors ([#121](https://github.com/Anthony-JCG/Platform/issues/121)) ([4076c70](https://github.com/Anthony-JCG/Platform/commit/4076c701b59edd2918b390799e36c69e8fac714e))

## [1.12.3](https://github.com/Anthony-JCG/Platform/compare/v1.12.2...v1.12.3) (2026-06-28)


### Bug Fixes

* **boards:** board page preview and mosaic sync ([#119](https://github.com/Anthony-JCG/Platform/issues/119)) ([34d3264](https://github.com/Anthony-JCG/Platform/commit/34d3264f7b31ce3f6a22d51d9ccebd83a11cafa7))

## [1.12.2](https://github.com/Anthony-JCG/Platform/compare/v1.12.1...v1.12.2) (2026-06-27)


### Performance Improvements

* **landing:** adjust profile image processing size ([#117](https://github.com/Anthony-JCG/Platform/issues/117)) ([e48501a](https://github.com/Anthony-JCG/Platform/commit/e48501a18c81bf942bedcaae2b36aa478da9e17d))

## [1.12.1](https://github.com/Anthony-JCG/Platform/compare/v1.12.0...v1.12.1) (2026-06-26)


### Bug Fixes

* **boards:** resolve PyMuPDF conflict and mosaic preview errors ([#115](https://github.com/Anthony-JCG/Platform/issues/115)) ([5ec432a](https://github.com/Anthony-JCG/Platform/commit/5ec432ac8b1e1e2134a5806dc3a4f9c834d7970a))

## [1.12.0](https://github.com/Anthony-JCG/Platform/compare/v1.11.0...v1.12.0) (2026-06-26)


### Features

* **keyboard-api:** mosaic previews, board updated_at, and delta sync ([#114](https://github.com/Anthony-JCG/Platform/issues/114)) ([05db2c0](https://github.com/Anthony-JCG/Platform/commit/05db2c05298982825b212a2e81c5a28fc3615aff))


### Performance Improvements

* **boards:** optimize mosaic preview loading ([#112](https://github.com/Anthony-JCG/Platform/issues/112)) ([54ce076](https://github.com/Anthony-JCG/Platform/commit/54ce076b3fef0ec2d0cc6a29f3d017912977281d))

## [1.11.0](https://github.com/Anthony-JCG/Platform/compare/v1.10.0...v1.11.0) (2026-06-24)


### Features

* **firebase:** initial integration setup ([#109](https://github.com/Anthony-JCG/Platform/issues/109)) ([d3ddcd1](https://github.com/Anthony-JCG/Platform/commit/d3ddcd1347b2a8ba1a7f0db6e3c7f7a781fa556f))
* **keyboard-api:** firebase offline sync for mobile keyboard ([#111](https://github.com/Anthony-JCG/Platform/issues/111)) ([8ecea2c](https://github.com/Anthony-JCG/Platform/commit/8ecea2c2274c2454328d78aac5f34bf13b096073))

## [1.10.0](https://github.com/Anthony-JCG/Platform/compare/v1.9.0...v1.10.0) (2026-06-22)


### Features

* **keyboard-api:** add mobile keyboard API for boards ([#105](https://github.com/Anthony-JCG/Platform/issues/105)) ([b0636ce](https://github.com/Anthony-JCG/Platform/commit/b0636ce8dddf94adc78599546b73cfd4e53a4e44))
* **sentry:** update sentry browser initialization and load script ([#102](https://github.com/Anthony-JCG/Platform/issues/102)) ([54108ee](https://github.com/Anthony-JCG/Platform/commit/54108ee4b5782cdda6192fe3df541937439bb1ec))


### Bug Fixes

* **boards:** stabilize page editor duplicate and sentry browser ([#100](https://github.com/Anthony-JCG/Platform/issues/100)) ([8669069](https://github.com/Anthony-JCG/Platform/commit/8669069cfa6293b01bec9d9ab456f7044e12d076))
* **boards:** suppress folder long-press on mobile drag ([#108](https://github.com/Anthony-JCG/Platform/issues/108)) ([2444625](https://github.com/Anthony-JCG/Platform/commit/244462594a38f27f1b59f5f5a837cbdca693d074))
* **files:** ensure image processing only if committed ([#101](https://github.com/Anthony-JCG/Platform/issues/101)) ([99f575d](https://github.com/Anthony-JCG/Platform/commit/99f575d1141862e444c7c5c0b9f0495b38fa6b7b))
* **keyboard-api:** json error and split endpoints ([#106](https://github.com/Anthony-JCG/Platform/issues/106)) ([69ff6fb](https://github.com/Anthony-JCG/Platform/commit/69ff6fbf18ec32018f1583ec45fc60c9879e97ee))
* **landing:** board editor, static deploy, and sentry ([#103](https://github.com/Anthony-JCG/Platform/issues/103)) ([73d36dc](https://github.com/Anthony-JCG/Platform/commit/73d36dc3a67755ef3cd0ebba083f49a04116c7f8))
* **notifications:** accept user id in push_notification ([#104](https://github.com/Anthony-JCG/Platform/issues/104)) ([fc0928e](https://github.com/Anthony-JCG/Platform/commit/fc0928e0411248c2f28bf8af180417e16f78ddd1))


### Code Refactoring

* **challenge:** eliminate technical debt and add service layer ([#97](https://github.com/Anthony-JCG/Platform/issues/97)) ([7262791](https://github.com/Anthony-JCG/Platform/commit/7262791986e3dce483574f257dd7f2101f93c2c2))
* eliminate technical debt across core, user_levels and boards ([#95](https://github.com/Anthony-JCG/Platform/issues/95)) ([9756aa8](https://github.com/Anthony-JCG/Platform/commit/9756aa8f3dd0c97210bd9a82a052221952c9dae7))
* **user_levels:** remove lru-cache era guards and clean up levels.py ([#98](https://github.com/Anthony-JCG/Platform/issues/98)) ([4defd8a](https://github.com/Anthony-JCG/Platform/commit/4defd8a2bdc7c4537e18ad84b7b273d29d37ed84))


### Documentation

* **readme:** translate user_levels, core and boards docs to english ([#99](https://github.com/Anthony-JCG/Platform/issues/99)) ([306ef0e](https://github.com/Anthony-JCG/Platform/commit/306ef0e834fc0e3dbf4add92de6807d5decfabd6))

## [1.9.0](https://github.com/Anthony-JCG/Platform/compare/v1.8.0...v1.9.0) (2026-06-17)


### Features

* **boards:** folder selection and rename ([#88](https://github.com/Anthony-JCG/Platform/issues/88)) ([f0762f6](https://github.com/Anthony-JCG/Platform/commit/f0762f6a8679ccd3228e4203d93f37be3ee6e00d))
* **boards:** mosaic masonry layout and item edit ([#87](https://github.com/Anthony-JCG/Platform/issues/87)) ([1e5960e](https://github.com/Anthony-JCG/Platform/commit/1e5960e4cf3f23c6ab33f52d16c3e53c09657f92))
* **boards:** native share, search viewer and destination picker ([#89](https://github.com/Anthony-JCG/Platform/issues/89)) ([0a77cef](https://github.com/Anthony-JCG/Platform/commit/0a77cefb7b0b18ff6e759950efbf3ead39d5bf14))
* **boards:** visibility permissions ([#84](https://github.com/Anthony-JCG/Platform/issues/84)) ([bf9cca4](https://github.com/Anthony-JCG/Platform/commit/bf9cca4f034781e4b94c0c74d923490349c1707b))
* **landing:** editor and public pages for boards ([#86](https://github.com/Anthony-JCG/Platform/issues/86)) ([3814492](https://github.com/Anthony-JCG/Platform/commit/3814492b7a8eaf71f4ffdc79612ebea4a054e214))
* **landing:** editor unified settings ([#85](https://github.com/Anthony-JCG/Platform/issues/85)) ([d9de186](https://github.com/Anthony-JCG/Platform/commit/d9de1864ca0ad7493158309263bb2e74561f579a))


### Bug Fixes

* **boards, landing:** banner, board page urls and mosaic edit ([#91](https://github.com/Anthony-JCG/Platform/issues/91)) ([2a2146f](https://github.com/Anthony-JCG/Platform/commit/2a2146f2eefb1e2abbb267b6cef57af4b92c04eb))
* **boards:** link preview audio ([#94](https://github.com/Anthony-JCG/Platform/issues/94)) ([cd85dad](https://github.com/Anthony-JCG/Platform/commit/cd85dad4f8cd83be88fdb99f4c36d4eeddd3c40a))
* **boards:** mosaic text tile, page preview and landing import ([#90](https://github.com/Anthony-JCG/Platform/issues/90)) ([4410069](https://github.com/Anthony-JCG/Platform/commit/441006965dc5e31882bbbf2bccd10cb266afff8a))
* **boards:** voice share cancel and playback duration ([#92](https://github.com/Anthony-JCG/Platform/issues/92)) ([ee638ef](https://github.com/Anthony-JCG/Platform/commit/ee638ef3784f229ab97828529b377551f3a1a860))
* **challenge:** reject empty daily task progress ([#82](https://github.com/Anthony-JCG/Platform/issues/82)) ([d5b32c7](https://github.com/Anthony-JCG/Platform/commit/d5b32c77dfaa8034372028b5d2cbf84fd0ed97fa))
* **config:** drop transient celery redis errors in sentry ([#81](https://github.com/Anthony-JCG/Platform/issues/81)) ([3ca7199](https://github.com/Anthony-JCG/Platform/commit/3ca7199d832e47bc6155ffa505805ceb37a62d61))
* **core:** validate push subscription before register ([#80](https://github.com/Anthony-JCG/Platform/issues/80)) ([bd83a4f](https://github.com/Anthony-JCG/Platform/commit/bd83a4f626b6032145e06687b2b1f5b7e9785149))
* **user_levels:** use correct variable ([#93](https://github.com/Anthony-JCG/Platform/issues/93)) ([07eb2fa](https://github.com/Anthony-JCG/Platform/commit/07eb2fade250007f88899f022d2592b1fdf02d1d))

## [1.8.0](https://github.com/Anthony-JCG/Platform/compare/v1.7.0...v1.8.0) (2026-06-09)


### Features

* **boards:** add cover image to board settings form ([#75](https://github.com/Anthony-JCG/Platform/issues/75)) ([84fc140](https://github.com/Anthony-JCG/Platform/commit/84fc140fdb7bd4c9ae41605f9163dc318b8da46f))
* **boards:** collaborators and mobile mosaic layout ([#76](https://github.com/Anthony-JCG/Platform/issues/76)) ([66ee9c9](https://github.com/Anthony-JCG/Platform/commit/66ee9c93c89cbe57f5036be539b6da9cee781a22))
* **boards:** share meta data ([#73](https://github.com/Anthony-JCG/Platform/issues/73)) ([2fbca97](https://github.com/Anthony-JCG/Platform/commit/2fbca97f6f2f14fa074d14cbfaafedb1e795149b))
* **landing:** add basic settings in content editor ([#77](https://github.com/Anthony-JCG/Platform/issues/77)) ([ed12735](https://github.com/Anthony-JCG/Platform/commit/ed12735f733c216db08031e05d56917c6be418e6))
* users birthday notifications ([#78](https://github.com/Anthony-JCG/Platform/issues/78)) ([dac045e](https://github.com/Anthony-JCG/Platform/commit/dac045e120b8638e72901bca527bc3f2ab85d727))


### Bug Fixes

* **boards:** route share links through share preview ([#79](https://github.com/Anthony-JCG/Platform/issues/79)) ([66dea6f](https://github.com/Anthony-JCG/Platform/commit/66dea6f87b25d10e16b5218a3bf5543a8d4976c6))

## [1.7.0](https://github.com/Anthony-JCG/Platform/compare/v1.6.2...v1.7.0) (2026-06-08)


### Features

* **landing:** add muted autoplay on public videos ([#66](https://github.com/Anthony-JCG/Platform/issues/66)) ([778acb6](https://github.com/Anthony-JCG/Platform/commit/778acb660ae9f9db6a3f12dbff932093d2f13849))
* **landing:** add share proxy config modal ([#68](https://github.com/Anthony-JCG/Platform/issues/68)) ([b178c5d](https://github.com/Anthony-JCG/Platform/commit/b178c5d6ccacff9f1c9816f3f3a07920bd3af5cf))
* **landing:** add wa button and footer colors ([#67](https://github.com/Anthony-JCG/Platform/issues/67)) ([369df1e](https://github.com/Anthony-JCG/Platform/commit/369df1e61725d9d7e23be556951d0f8113a5b57a))
* new page my boards ([#69](https://github.com/Anthony-JCG/Platform/issues/69)) ([3c26d80](https://github.com/Anthony-JCG/Platform/commit/3c26d802c621b92d1d11d30f8fa548dbdbd5e429))


### Bug Fixes

* **landing:** keep wa blink in dom for ios safari ([#64](https://github.com/Anthony-JCG/Platform/issues/64)) ([549e9b9](https://github.com/Anthony-JCG/Platform/commit/549e9b9648840bd1672cce7f257c11758a586b2d))
* **landing:** update communication dependency in migrations ([#70](https://github.com/Anthony-JCG/Platform/issues/70)) ([dc4a673](https://github.com/Anthony-JCG/Platform/commit/dc4a6735f0a85934abd53d37ebb7376dd1602e7e))

## [1.6.2](https://github.com/Anthony-JCG/Platform/compare/v1.6.1...v1.6.2) (2026-06-04)


### Bug Fixes

* **notifications:** expose vapid key and stabilize push delivery ([#62](https://github.com/Anthony-JCG/Platform/issues/62)) ([a269041](https://github.com/Anthony-JCG/Platform/commit/a269041924fda894994057ad9cc70ec7f13b3dc9))

## [1.6.1](https://github.com/Anthony-JCG/Platform/compare/v1.6.0...v1.6.1) (2026-06-04)


### Bug Fixes

* docker celerybeat permissions ([#60](https://github.com/Anthony-JCG/Platform/issues/60)) ([8715db1](https://github.com/Anthony-JCG/Platform/commit/8715db1eff747e2c6ba3e0bc8631d961ae9d8de9))
* main webpush celerybeat ([#57](https://github.com/Anthony-JCG/Platform/issues/57)) ([ce748c3](https://github.com/Anthony-JCG/Platform/commit/ce748c3f0b62fd09896770e2220df66dbec940c5))
* **user_levels:** change default user level profile to basic ([#61](https://github.com/Anthony-JCG/Platform/issues/61)) ([b840de4](https://github.com/Anthony-JCG/Platform/commit/b840de4a8e6774979d1cb27ad00132a03f55655d))

## [1.6.0](https://github.com/Anthony-JCG/Platform/compare/v1.5.0...v1.6.0) (2026-06-03)


### Features

* user levels subscription correction ([#56](https://github.com/Anthony-JCG/Platform/issues/56)) ([d64e251](https://github.com/Anthony-JCG/Platform/commit/d64e2510fe3d4ac8a4999276f99658560f25408b))


### Bug Fixes

* **level_code:** users sentry unpaid level alert ([#55](https://github.com/Anthony-JCG/Platform/issues/55)) ([23f9955](https://github.com/Anthony-JCG/Platform/commit/23f9955dfe8c9158972b0208798848fa36001abb))
* **users:** stop activating free trial on training ([#53](https://github.com/Anthony-JCG/Platform/issues/53)) ([a44a565](https://github.com/Anthony-JCG/Platform/commit/a44a565bd8ae9e28f8d3634c91d5b13cd4ab6099))

## [1.5.0](https://github.com/Anthony-JCG/Platform/compare/v1.4.0...v1.5.0) (2026-06-01)


### Features

* sentry logging integration ([#38](https://github.com/Anthony-JCG/Platform/issues/38)) ([8e509bf](https://github.com/Anthony-JCG/Platform/commit/8e509bf055d25023c1e53e0396edc9b9a0984713))


### Bug Fixes

* **landing:** adjust animation duration and button class ([#39](https://github.com/Anthony-JCG/Platform/issues/39)) ([01cc20a](https://github.com/Anthony-JCG/Platform/commit/01cc20a4d8bf423cb9ff048ac1c83502567428d0))
* **landing:** update button padding direction in whatsapp button template ([#40](https://github.com/Anthony-JCG/Platform/issues/40)) ([49fcf4e](https://github.com/Anthony-JCG/Platform/commit/49fcf4ebce36ec256b8482bb726084ea1ad48a0a))


### Code Refactoring

* **landing:** refactor landing code ([#35](https://github.com/Anthony-JCG/Platform/issues/35)) ([6a3d81a](https://github.com/Anthony-JCG/Platform/commit/6a3d81aa7f6897e9dbb3d2ac9b27cbfa4b80a8b2))


### Documentation

* **landing:** add README documentation for landing app ([#37](https://github.com/Anthony-JCG/Platform/issues/37)) ([eebae29](https://github.com/Anthony-JCG/Platform/commit/eebae29cfd1a8b4ea3a48d4191ff142dfc0c64c0))

## [1.4.0](https://github.com/Anthony-JCG/Platform/compare/v1.3.0...v1.4.0) (2026-05-29)


### Features

* **landing:** landing page available to everyone ([#31](https://github.com/Anthony-JCG/Platform/issues/31)) ([3b27dc1](https://github.com/Anthony-JCG/Platform/commit/3b27dc1d68f0b217d8008b0f1bf63f299e0658a4))

## [1.3.0](https://github.com/Anthony-JCG/Platform/compare/v1.2.0...v1.3.0) (2026-05-29)


### Features

* **landing:** landing block backgrounds ([#23](https://github.com/Anthony-JCG/Platform/issues/23)) ([b080560](https://github.com/Anthony-JCG/Platform/commit/b0805605097c9178387075555534b04d0e0286ac))
* **landing:** landing page break ([#20](https://github.com/Anthony-JCG/Platform/issues/20)) ([c8da198](https://github.com/Anthony-JCG/Platform/commit/c8da198b90cd880a3596092d5b9a6d454e0b37c1))
* **landing:** landing permissions ([#28](https://github.com/Anthony-JCG/Platform/issues/28)) ([5cf41ab](https://github.com/Anthony-JCG/Platform/commit/5cf41ab3b0e25c16894056588004f95a5a750524))


### Bug Fixes

* **ci:** lint only PR-changed Python files with Ruff ([#22](https://github.com/Anthony-JCG/Platform/issues/22)) ([4283d02](https://github.com/Anthony-JCG/Platform/commit/4283d0290c2947dc354fd1f96d2715db2a405e7c))
* **crousel-landing:** landing mobile carousel ([#26](https://github.com/Anthony-JCG/Platform/issues/26)) ([3f66cb6](https://github.com/Anthony-JCG/Platform/commit/3f66cb62fc587fe15bd97e90e4d3becc97624609))
* landing quill styles ([#24](https://github.com/Anthony-JCG/Platform/issues/24)) ([b6a1986](https://github.com/Anthony-JCG/Platform/commit/b6a19863c125228774577257e54f2a9c074e54bf))
* **landing:** allow empty learnings section title on save and render ([#25](https://github.com/Anthony-JCG/Platform/issues/25)) ([e48854c](https://github.com/Anthony-JCG/Platform/commit/e48854cdd88a5842db4999d34b35de3930ed6f53))
* **learnings landing:** landing learning text ([#27](https://github.com/Anthony-JCG/Platform/issues/27)) ([c0f4d99](https://github.com/Anthony-JCG/Platform/commit/c0f4d99cffb3f3d72a50876893a1fae07a8ff782))

## [1.2.0](https://github.com/Anthony-JCG/Platform/compare/v1.1.0...v1.2.0) (2026-05-28)


### Features

* **landing:** visual landing constructor ([#17](https://github.com/Anthony-JCG/Platform/issues/17)) ([81c3ebe](https://github.com/Anthony-JCG/Platform/commit/81c3ebe178741388387c032127924a3c0ecc313e))


### Code Refactoring

* reestructure django apps ([#14](https://github.com/Anthony-JCG/Platform/issues/14)) ([35f967f](https://github.com/Anthony-JCG/Platform/commit/35f967f7da54fb82d8927d8bad1dddaad10132f2))

## [1.1.0](https://github.com/Anthony-JCG/Platform/compare/v1.0.0...v1.1.0) (2026-05-27)


### Features

* add 'free_trial_active' to list display and filter in UserLevelProfileAdmin ([e3bd2ba](https://github.com/Anthony-JCG/Platform/commit/e3bd2ba6c80423343b4a07f65eb40f230b8f9fd4))
* add 'soon' parameter to waiting page option and return 404 status in waiting_page view ([84cf02b](https://github.com/Anthony-JCG/Platform/commit/84cf02b94c73e37e6e51f633e31498365dabf015))
* add action message field to scheduled tasks and enhance follow-up message handling ([40babfe](https://github.com/Anthony-JCG/Platform/commit/40babfe14e7eccb30b8fd2eb76194daae47c19ce))
* add AJAX support for deleting landing blocks and enhance landing page save functionality ([e4d1571](https://github.com/Anthony-JCG/Platform/commit/e4d1571855b1853a8b0e99aa5f9458fa13eb5fd6))
* add background image field to CategoryTraining model ([45910ef](https://github.com/Anthony-JCG/Platform/commit/45910ef05d5659075a83ab3caf396579f05f20cb))
* add background image field to incentives and update form handling for file uploads ([ac8da0c](https://github.com/Anthony-JCG/Platform/commit/ac8da0c028d3d5b21c658650ff16863dfb9471f8))
* add block label updates and refactor undo delete component ([5b19e0b](https://github.com/Anthony-JCG/Platform/commit/5b19e0b0178e3a00ae788b8dfca607aa67801e87))
* add busy state handling for save buttons to improve user feedback during async operations ([73147ac](https://github.com/Anthony-JCG/Platform/commit/73147acce454adb5b3df686e1c12a26d8c2f0077))
* add carousel formset management and enhance landing page customization ([553d514](https://github.com/Anthony-JCG/Platform/commit/553d514b89524bfee53d8ffa8698df72aedf8f8a))
* add category cover image and progress display to category component ([b6a9ac3](https://github.com/Anthony-JCG/Platform/commit/b6a9ac3ccda452d316ccb83051e3ff10f2f36910))
* add conditional pricing page access based on user permissions ([f351995](https://github.com/Anthony-JCG/Platform/commit/f351995e40cbae79036698ae0800400b6ece70f1))
* add conditional pricing page access based on user permissions ([6731f3c](https://github.com/Anthony-JCG/Platform/commit/6731f3c1959fce5e6c300a0f46f3a89147ff3619))
* add confirmation modals for membership status deletion and toggling ([c89b0ee](https://github.com/Anthony-JCG/Platform/commit/c89b0eebd3851655d7406858b24013d97f5b4262))
* add course card component and training course formations view ([d925c8c](https://github.com/Anthony-JCG/Platform/commit/d925c8c7484456bd1099fb1e212033538ab2c526))
* add CSRF token to modal footer for enhanced security ([7e711e7](https://github.com/Anthony-JCG/Platform/commit/7e711e75d33769786b507e61c4d55beeaa0b9914))
* add CSRF token to personal info form for security ([7a006f3](https://github.com/Anthony-JCG/Platform/commit/7a006f3eae30676f2312fb8ef6487b3d0a01ea51))
* add custom filter for Stripe customer status in admin user list ([bcc5063](https://github.com/Anthony-JCG/Platform/commit/bcc50634ada8825e7c56d0f124797b7cfb109650))
* add data attribute to date of birth select widget for improved handling ([341d997](https://github.com/Anthony-JCG/Platform/commit/341d997204e8ef2cf6a0b1b3d4f0f9662e6eac65))
* add data attribute to training video modal for body restoration control ([0b89cee](https://github.com/Anthony-JCG/Platform/commit/0b89cee39fc5666bd6a138d9999f6a2073b7d236))
* add debug logging for modal control and enhance Quill input synchronization ([ecd945c](https://github.com/Anthony-JCG/Platform/commit/ecd945cf8fa2121cc0fdc89f01293efb22d4dde7))
* add debug server host to trusted origins in settings ([5f6977e](https://github.com/Anthony-JCG/Platform/commit/5f6977e6dc0ca8c617c39d31ff4b6a933eadd653))
* add default values for resource name and URL fields in models ([2588096](https://github.com/Anthony-JCG/Platform/commit/25880961468f251c86bf1a87012b0d5265d6d602))
* add downgrade block handling for live streams in waiting page ([1f0c2d4](https://github.com/Anthony-JCG/Platform/commit/1f0c2d46f2c727c85883c06804466f594187c2c4))
* add downgrade_task_id field and enhance user profile downgrade handling ([f4c4126](https://github.com/Anthony-JCG/Platform/commit/f4c412604ecbcae2225e64974a145cf87486a389))
* add email contact button for users in invited users and team displays ([d72ef2a](https://github.com/Anthony-JCG/Platform/commit/d72ef2a4edabcf6b72c075fb034f7d25d1801be2))
* add email notification for sponsors when a user completes a category ([e28d425](https://github.com/Anthony-JCG/Platform/commit/e28d4251dbfc569da8a1df4cf78cbe3071c8ce50))
* add email templates and functions for subscription creation and cancellation notifications ([00e36f8](https://github.com/Anthony-JCG/Platform/commit/00e36f8874e7592e2f64ca1584a9b81c17a4d98a))
* add email templates for subscription cancellation, upgrade, and downgrade notifications ([8612ea6](https://github.com/Anthony-JCG/Platform/commit/8612ea620174e5a3fdaaac24fa897c60c890dded))
* add file attachment support to route steps and enhance progress tracking display ([5fce4c7](https://github.com/Anthony-JCG/Platform/commit/5fce4c7794d31d3d4b2beb2566f93e2bacd8c88b))
* add file size validation for uploads, limiting to 4.99 GB ([18c0b76](https://github.com/Anthony-JCG/Platform/commit/18c0b7652617f91fcec2a1750ed3f4dd7377c803))
* add filtering for blocked direct streams in own streams query ([9ca1fda](https://github.com/Anthony-JCG/Platform/commit/9ca1fdae9c11b7c6d5568d3694586422d2f3148e))
* add FIRST_LEADER_PRO constant and update notification logic for specific user ([d64867b](https://github.com/Anthony-JCG/Platform/commit/d64867b19c9f62b34d524c97ff75369e4e15c969))
* add floating search backdrop and enhance locked category indication in search results ([472de7b](https://github.com/Anthony-JCG/Platform/commit/472de7b970cf1a5fae5299fd03e41327c76f1c38))
* add follow-up contact message customization model and related form updates ([b5223fa](https://github.com/Anthony-JCG/Platform/commit/b5223fa4f18f0e8131c9a0ae24971f4ebb47002d))
* add follow-up contact message customization model and related form updates ([fc9eef8](https://github.com/Anthony-JCG/Platform/commit/fc9eef882545d184c4f7ccfe50f3adb0f9bc81e3))
* add follow-up message functionality with related form and view updates ([3e3e7a7](https://github.com/Anthony-JCG/Platform/commit/3e3e7a7075458517168355671462b688049fc785))
* add form reference to autosave fetch request for improved data handling ([96068c0](https://github.com/Anthony-JCG/Platform/commit/96068c0acc13fb8ccf19a5885b15c50f73225b8b))
* add form validation helper and streamline error handling in views ([e4ab998](https://github.com/Anthony-JCG/Platform/commit/e4ab998ce70d1afff04533b778fc94536765750e))
* add function to check active Stripe subscription for users ([a67010e](https://github.com/Anthony-JCG/Platform/commit/a67010e2346fb3e12047b49111389f437c554394))
* add geocoding functionality to map and configure search control for improved location selection ([b374b59](https://github.com/Anthony-JCG/Platform/commit/b374b59f7f8573ca4a2087fd3a0f454c5d007c9e))
* add get_prices method to plan model and update pricing display in templates ([7892904](https://github.com/Anthony-JCG/Platform/commit/7892904d8aba010c31719a947949bcbb0710fff9))
* add global confirmation modal for action confirmations and enhance delete step functionality ([9647e1f](https://github.com/Anthony-JCG/Platform/commit/9647e1ff23656d6c38ca90e6923be3c8bc238c55))
* add global page loading overlay for navigation ([2c32eea](https://github.com/Anthony-JCG/Platform/commit/2c32eead1d4e1173c17fa9155f02d8751e5cf3bf))
* add global search functionality with floating search button and results display ([7e9d1dd](https://github.com/Anthony-JCG/Platform/commit/7e9d1dd1e631f5a6142aa0f827a574501e63cff8))
* add hidden category functionality with access management for users ([3ada17d](https://github.com/Anthony-JCG/Platform/commit/3ada17dd4ea7f12d27abd9cab91ebccdc13dae2d))
* add import streams functionality for leaders and PRO users ([9b91be3](https://github.com/Anthony-JCG/Platform/commit/9b91be37fabf36d1a4739c65889ad08db09339d8))
* add IncentiveFile model and implement file upload functionality in incentives ([877ea7a](https://github.com/Anthony-JCG/Platform/commit/877ea7a60993f905c721b1b2ee8d555dd134cc3a))
* add instructional block for PRO users in waiting page and improve table structure ([154e10c](https://github.com/Anthony-JCG/Platform/commit/154e10cae362045028d69620e249a4eb2bf98d04))
* add is_shared_object field to streaming model and update related forms and views ([fbcbfd3](https://github.com/Anthony-JCG/Platform/commit/fbcbfd3cd3b43693857b320580de3e9efe5c37e4))
* add landing page block management with dynamic content handling ([cc6e6f9](https://github.com/Anthony-JCG/Platform/commit/cc6e6f90da839adbef236cb93fe3ebfcddf1d056))
* add learnings section title to landing page block with default value and update form handling ([48209d7](https://github.com/Anthony-JCG/Platform/commit/48209d7c36f6a5f8bc889f3a41ca21d41a7bd4b5))
* add level visibility functions and enhance notification logic with allowed levels ([ebffeb8](https://github.com/Anthony-JCG/Platform/commit/ebffeb8b62b09e0102eeeeb388beb11aff4acffe))
* add list_editable options for LevelAdmin and UserLevelProfileAdmin ([c5070cd](https://github.com/Anthony-JCG/Platform/commit/c5070cdadaa33b2e933c407d312fd1288fd9cea1))
* add loading spinner to submit buttons for forms without file uploads ([dc1c213](https://github.com/Anthony-JCG/Platform/commit/dc1c21397051e9b9e5898421247a4df8dea0df9c))
* add location fields to incentives and implement map functionality for better visualization ([e458ce4](https://github.com/Anthony-JCG/Platform/commit/e458ce4952c14ade64baad64d4a0c0f73eed923b))
* add logging for task fetching and UI updates, include target value in task response ([4746835](https://github.com/Anthony-JCG/Platform/commit/474683570cb0ec24d3e1893270f8ff4f60dc8a4d))
* add management command to clean stale notifications from Redis ([29bc0cb](https://github.com/Anthony-JCG/Platform/commit/29bc0cb4e59748f2ec4ef49832c5a11736f71ed7))
* add management command to clean stale notifications from Redis ([c2b264f](https://github.com/Anthony-JCG/Platform/commit/c2b264fadaf2b7fefbd290fe9b2796df168b1fb1))
* add max_length to ImageField for speaker and host photos, and update slider image model ([333aa80](https://github.com/Anthony-JCG/Platform/commit/333aa80d84f9f27e21258dfff5019880616199e0))
* add method to generate short URL and update iframe source in link-mate ([cc024b2](https://github.com/Anthony-JCG/Platform/commit/cc024b2e8c40fe4e655aec1221ad8c725545911b))
* add mini contact form for stream registration and implement email reminder task ([a051718](https://github.com/Anthony-JCG/Platform/commit/a0517186a61d30855c517d88d3a952b6abf05b5f))
* add modal and button for viewing plans, enhancing user navigation ([0322836](https://github.com/Anthony-JCG/Platform/commit/032283669ccbaf5849e9c127c47637228b09eb4e))
* add modal subsection component and enhance form handling in training course formations ([215cc72](https://github.com/Anthony-JCG/Platform/commit/215cc7251e13b4924d72673c1bde89a5a076c0f1))
* add order field to TypeIncentive model and update TypeIncentiveForm to include name only ([5bde002](https://github.com/Anthony-JCG/Platform/commit/5bde002b7409f88e54c5e0bd348e49e762320c8f))
* add personal tasks section to challenge management and update views for better task handling ([05f2d72](https://github.com/Anthony-JCG/Platform/commit/05f2d72fed4917b8bc389108979448aa51f86090))
* add phone field to personal data section and maintain field order logic ([b97b6cd](https://github.com/Anthony-JCG/Platform/commit/b97b6cdcef96d12ccf5bb8ab0de6faca89346974))
* add post page slider script to waiting page ([81f371a](https://github.com/Anthony-JCG/Platform/commit/81f371a03eab06d17b0a90eb7d997b7860dfe83e))
* add preview mode for stream and post pages, including new views and UI alerts ([f09a026](https://github.com/Anthony-JCG/Platform/commit/f09a0267f62f5e00309332aa4233d31eb0258253))
* add Quill image viewer functionality and update HTML structure for image rendering ([abe9a93](https://github.com/Anthony-JCG/Platform/commit/abe9a930590d147e5a67ab93d4635ad273e43e85))
* add recurrence functionality to streaming model and forms for leader PRO users ([557b97d](https://github.com/Anthony-JCG/Platform/commit/557b97dffe4af5d551249045140d34b0d3a627bb))
* add referrer policy to enhance security and update incentive card rendering for improved maintainability ([109596b](https://github.com/Anthony-JCG/Platform/commit/109596b68bf03ffc852fc374a6a769d27f217261))
* add save_type_incentive endpoint and update templates for user root access ([bf59838](https://github.com/Anthony-JCG/Platform/commit/bf598387c10d41c7a1f242dd55a4619011571d4c))
* add share preview page with Open Graph and Twitter meta tags ([8e63388](https://github.com/Anthony-JCG/Platform/commit/8e633887e8cc241fe5e22454fe106f3741820542))
* add simplified forms for PRO users and enhance waiting page functionality ([8a4820e](https://github.com/Anthony-JCG/Platform/commit/8a4820e01ea99323eb73a167a320dae280dde029))
* add Stripe API keys to settings and update requirements ([7790adc](https://github.com/Anthony-JCG/Platform/commit/7790adc416831bb6bffe415c237debc1d40e91b5))
* add support for multiple activity photos with upload limit and display ([1f87437](https://github.com/Anthony-JCG/Platform/commit/1f87437d319edef1533a3dd3bf1b4a6f9deae334))
* add support for new LevelType and improve photo validation in tests ([a0f4877](https://github.com/Anthony-JCG/Platform/commit/a0f4877a12e66fa75e0f5a086a784b9ded76cea2))
* add support for Stripe API keys and webhook configuration ([4023c36](https://github.com/Anthony-JCG/Platform/commit/4023c360a4ae7c7bde17c9641b49cac1cf483abf))
* add TEST_ENVIRONMENT configuration to manage cookie sharing in test and production environments ([7e43ae0](https://github.com/Anthony-JCG/Platform/commit/7e43ae0163ae9fc6c2cb58e84df967093240c537))
* add TEST_ENVIRONMENT support to adjust grace periods for downgrades and trials ([656019a](https://github.com/Anthony-JCG/Platform/commit/656019ab170db5bfeddf2b1881e081d137c1eca3))
* add text color customization for landing page ([7df82d3](https://github.com/Anthony-JCG/Platform/commit/7df82d36276ca64458de10e59d30d4bf722881f4))
* add tracker field to RouteStepProgress model and update related logic ([015c5b7](https://github.com/Anthony-JCG/Platform/commit/015c5b7de04fe5aa3d1185722f7addeceae480b9))
* add training video modal and integrate dynamic video loading functionality ([d5de64d](https://github.com/Anthony-JCG/Platform/commit/d5de64d6e575cd3b8b92cb46557200ca3ee845d7))
* add translation support to email templates for live streams ([bfdc424](https://github.com/Anthony-JCG/Platform/commit/bfdc42462ed2ad56980ab97d38adc958c47987bb))
* add unmute overlay and enhance mute/unmute button functionality in stream player ([069a84f](https://github.com/Anthony-JCG/Platform/commit/069a84f364553c7ed06fb72537546e0fd804b751))
* add user level code to enhance location detail visibility based on user plan ([ba265ee](https://github.com/Anthony-JCG/Platform/commit/ba265eefc62d372879c408cf164c541597edbbe7))
* add utility functions for effective subsection retrieval and message handling ([400c626](https://github.com/Anthony-JCG/Platform/commit/400c6268685576c35034ea12f025eb2cc5d53bf1))
* add validation for required fields in incentive form and enhance field labels ([04df5bb](https://github.com/Anthony-JCG/Platform/commit/04df5bb1811e82a9500116807293ad9a56c91014))
* add verbose name to block_type field in models ([0e16d52](https://github.com/Anthony-JCG/Platform/commit/0e16d522729b67b6cf518b69f3cba59b878ad2c5))
* add was_leader_when_downgraded field to track leader status during downgrade ([93442d9](https://github.com/Anthony-JCG/Platform/commit/93442d9e0d8a33df66c1f58b28f5270e8831aef7))
* add welcome email functionality for new users upon registration ([07baecb](https://github.com/Anthony-JCG/Platform/commit/07baecbf0f4d2726bdc956558660856aaf906fae))
* add WhatsApp message generation and URL for scheduled tasks ([c182835](https://github.com/Anthony-JCG/Platform/commit/c182835d603f063dc6699a0d7c2550582b08462c))
* adjust card layout and styling for simplified view ([4f7b183](https://github.com/Anthony-JCG/Platform/commit/4f7b183578f35434d122f3a6d637e6aaa7d11189))
* adjust floating search wrapper positioning for better responsiveness on small screens ([a744766](https://github.com/Anthony-JCG/Platform/commit/a744766197514c37ebef09fae08faec3bc13eeb1))
* adjust floating search wrapper positioning for improved responsiveness ([2e2c25c](https://github.com/Anthony-JCG/Platform/commit/2e2c25c3bbb8145fa821dfd5ad7098ff0d294ce3))
* adjust lazy loading generation for user children and update button state in invited users tree ([45da562](https://github.com/Anthony-JCG/Platform/commit/45da562367d0650af714ee73ce7e5ac17ae55422))
* adjust max-height of daily challenges scroll in challenge overview card ([2a8318b](https://github.com/Anthony-JCG/Platform/commit/2a8318bc25c2bdfea2e0c87519bd2aa41ea68545))
* adjust section title font size for improved readability ([b0af8f6](https://github.com/Anthony-JCG/Platform/commit/b0af8f6dcf22dce4e8814b6678ab18f94a452940))
* adjust subsection title font size and update training course link for improved layout ([d314d35](https://github.com/Anthony-JCG/Platform/commit/d314d35a42e5ad32b48a9b130251dde6d741210a))
* alter contact membership field choices for improved clarity and options ([aa131dc](https://github.com/Anthony-JCG/Platform/commit/aa131dcf010f6699057d2a6ee9ac5b3dbd2203c1))
* alter typeincentive model options to set ordering by order and created_at ([d5af29b](https://github.com/Anthony-JCG/Platform/commit/d5af29b8707c0d6d460bbee62bc017f8843a96f3))
* alter user field in Subsection model to allow null values ([fa2aba3](https://github.com/Anthony-JCG/Platform/commit/fa2aba3e0f28806847d3e1c1d63572dde7ef8be3))
* alter user field in Subsection model to allow null values ([1624b61](https://github.com/Anthony-JCG/Platform/commit/1624b61b921cf83b66e8733127aaf759240d7608))
* apply line breaks to how qualification text in incentives ([8634cae](https://github.com/Anthony-JCG/Platform/commit/8634caec794ae3144ef797da77fc277477732953))
* clean up admin imports and add WHA_LINK_MODEL_KEY to capabilities ([931b651](https://github.com/Anthony-JCG/Platform/commit/931b651429c7338f1437c5e03df82558893263f9))
* comment out navigation item for loyalty cards in contact modal ([36df82e](https://github.com/Anthony-JCG/Platform/commit/36df82ece40ff0cb41975063a644b7a2ca4c6069))
* conditionally display back-to-top link for authenticated users ([bae6bcb](https://github.com/Anthony-JCG/Platform/commit/bae6bcbe5fb5347a881ef60e9712cf8ab62c2898))
* configure file upload handlers and memory size limits for large uploads in Django ([da9d65a](https://github.com/Anthony-JCG/Platform/commit/da9d65a3bbcc9ab2b607d3a20460aaddff8f78b9))
* configure file upload handlers and memory size limits for large uploads in Django ([8644c3a](https://github.com/Anthony-JCG/Platform/commit/8644c3af8651cb42e527e81511d642108755abca))
* configure file upload handlers and memory size limits for large uploads in Django ([5051420](https://github.com/Anthony-JCG/Platform/commit/5051420b72edcd2176aa92c9f815b0b77cc39699))
* correct email address in contacto_info to use support instead of soporte ([cb2179a](https://github.com/Anthony-JCG/Platform/commit/cb2179a105720c7b084ffb3a12b41bb38ff8ba4c))
* create modal for viewer registration and update membership default to 'prospect' ([4f4c630](https://github.com/Anthony-JCG/Platform/commit/4f4c630c0e2242d881d2ee57c5e3a9f09ef60f00))
* create TypeIncentive model and update Incentive to use foreign key relationship ([86a2ba9](https://github.com/Anthony-JCG/Platform/commit/86a2ba9a3ed270b163733ca8e682796eb9877682))
* **css:** add blink animation with reduced motion support ([273b0e5](https://github.com/Anthony-JCG/Platform/commit/273b0e51c24e18f85c078ac35a7d1b9d73f43036))
* customize subsection form field IDs to avoid ID collisions in modals ([547721c](https://github.com/Anthony-JCG/Platform/commit/547721c8ea65c1d83ec0e8643f67a4b8a4f71727))
* display debug environment alert in main layout ([2df4c45](https://github.com/Anthony-JCG/Platform/commit/2df4c4563d292e3d560fd9ab70854720b48634c0))
* enable editing of the first formation in training course view with improved context handling ([6d3af16](https://github.com/Anthony-JCG/Platform/commit/6d3af16bafd824c3c2ff72aaabc626f1d742b8df))
* enforce email requirement in form and improve file upload handling in models ([46ad25f](https://github.com/Anthony-JCG/Platform/commit/46ad25f0acd21a2b057d1e0d0ef107b35618cec0))
* enhance authentication flow with invitation-only access and review request modal ([ec9d98b](https://github.com/Anthony-JCG/Platform/commit/ec9d98bd7ce41472307bdc5bbbf2f2e2f094c204))
* enhance BFS implementation for user retrieval with improved node processing and visit tracking ([88b9110](https://github.com/Anthony-JCG/Platform/commit/88b911056b27f3adab4ac1912d0d0c53fdf868fa))
* enhance button accessibility and layout in filters and ordering section ([4f4ec71](https://github.com/Anthony-JCG/Platform/commit/4f4ec710cb02e25b6fcd5962a43dbf379abdb450))
* enhance button copy functionality with icon and color customization ([4dfc5a5](https://github.com/Anthony-JCG/Platform/commit/4dfc5a533dccdcf0fa39ded83718916f2ccc3b60))
* enhance button functionality and improve price handling in Stripe utilities ([11b9fa1](https://github.com/Anthony-JCG/Platform/commit/11b9fa1efda7dd0474736256a838130e9fe53ed7))
* enhance button styling and improve incentive card layout ([0ba0de2](https://github.com/Anthony-JCG/Platform/commit/0ba0de2591a4be13bde4a5b1972e8aa9188d6d40))
* enhance carousel styling and improve checkbox input handling ([3ed2c02](https://github.com/Anthony-JCG/Platform/commit/3ed2c02e88f8785e0e35c213a6f2ea8f24cd2d4f))
* enhance category and course card components with improved layout and accessibility ([0383ccb](https://github.com/Anthony-JCG/Platform/commit/0383ccb9cfb881a7ac4ccc07c676376242dea858))
* enhance category and section access logic for first steps training mode ([de1ed0b](https://github.com/Anthony-JCG/Platform/commit/de1ed0b05c50b18b0dbcd53b7319c913e98b59be))
* enhance category and section access management for edit mode ([b28c97b](https://github.com/Anthony-JCG/Platform/commit/b28c97be21bc3443b4f093982bbbacf8675bcc1d))
* enhance category and section modals with improved data handling and rendering ([6292e5b](https://github.com/Anthony-JCG/Platform/commit/6292e5bc18da384d85af6b6fb0272219578b7f1c))
* enhance category and section templates with tooltips and optional fields ([0982b75](https://github.com/Anthony-JCG/Platform/commit/0982b7539f5479a5cf7aeb9433042f6807a0a2ed))
* enhance category display with new badges and dynamic styling for completed and new categories ([cb8efd3](https://github.com/Anthony-JCG/Platform/commit/cb8efd3dc96cdb4cb4a99a15592e69e68d340f63))
* enhance category filtering for leader pro and improve subsection retrieval logic ([c4c7f17](https://github.com/Anthony-JCG/Platform/commit/c4c7f17fb384209455dfb610df16ccc4e4f512b6))
* enhance category progress calculation and reset invitation form after sending ([99c93f9](https://github.com/Anthony-JCG/Platform/commit/99c93f9add85bddd053c19c63dfffbf269a7a0e0))
* enhance challenge management with improved redirection and personal tasks section ([aa18b8e](https://github.com/Anthony-JCG/Platform/commit/aa18b8ed9b9917a03429268fab34880d3a4c1fca))
* enhance collect_downgrade_blocks function to exclude personal challenges from downgrade flags ([ff2ec81](https://github.com/Anthony-JCG/Platform/commit/ff2ec813be0c606ffb4598288c972b7b314b038a))
* enhance CSRF token handling and streamline fetch requests with automatic token management ([49afa35](https://github.com/Anthony-JCG/Platform/commit/49afa350ec7d503fe33fb8da00f5393cdc87be86))
* enhance daily tasks display to include downgrade block handling and personal challenge exclusions ([681cc66](https://github.com/Anthony-JCG/Platform/commit/681cc666392b2f6285b2707cf054b53bb46591e6))
* enhance debugging information and update caching strategy in service worker ([340aa6e](https://github.com/Anthony-JCG/Platform/commit/340aa6e9f58a18e7407475b0a40b59e071e30920))
* enhance downgrade handling by adding leader downgrade flags and updating excess object management ([7d80235](https://github.com/Anthony-JCG/Platform/commit/7d802356cf0dec0ecb8f080275fb9115278eb502))
* enhance downgrade handling by adding leader downgrade flags and updating excess object management ([390d683](https://github.com/Anthony-JCG/Platform/commit/390d683febd48c4e9fd078e3c52c4c9b5ea787a7))
* enhance downgrade handling by adding task and message models to downgrade logic and UI updates ([a401a3e](https://github.com/Anthony-JCG/Platform/commit/a401a3ecb026a2c0e5873674164a7221baabc4d0))
* enhance downgrade handling by adding task and message models to downgrade logic and UI updates ([6b0b25b](https://github.com/Anthony-JCG/Platform/commit/6b0b25bd1fd46e089a39c96f202281702b61b5cd))
* enhance drag-and-drop functionality for leaders with updated cursor styles ([126e552](https://github.com/Anthony-JCG/Platform/commit/126e552266d82218a5fa13568533a6512ff64d29))
* enhance favorite incentives toggle functionality to support incentive type handling ([b8567ce](https://github.com/Anthony-JCG/Platform/commit/b8567ceba6b4dc6bf85330ecf53b52b3a1f116ad))
* enhance file upload handling in landing page components with new preview functionality and modular file field widget ([6a586af](https://github.com/Anthony-JCG/Platform/commit/6a586afcd0817296b22f30e3d27d428469ba211b))
* enhance floating search backdrop opacity and clean up return statement in views ([c859f35](https://github.com/Anthony-JCG/Platform/commit/c859f35b5a1e4f726cedd04427f63eb649c09bb2))
* enhance floating search results with absolute URLs and improved action buttons ([3c8d7a6](https://github.com/Anthony-JCG/Platform/commit/3c8d7a6e910e5d69e2ff44bada3a52050fd058c8))
* enhance form field restrictions for basic and pro levels, adding host and speaker data handling ([e610d52](https://github.com/Anthony-JCG/Platform/commit/e610d5225cd216fafbf57869393a91584d37082b))
* enhance form handling and improve data management in modals and views ([5680d1a](https://github.com/Anthony-JCG/Platform/commit/5680d1a382273cffa1380671432767122b8cd685))
* enhance form inputs with improved tooltip handling and password visibility toggle ([52376d8](https://github.com/Anthony-JCG/Platform/commit/52376d86a2468154721017400dd4a101a31ef689))
* enhance form sections with dynamic labels and tooltips for better user guidance ([b081900](https://github.com/Anthony-JCG/Platform/commit/b081900355dc733f84584f11bf4039181a4469b2))
* enhance form submission handling with spinner support for file uploads ([cf7550f](https://github.com/Anthony-JCG/Platform/commit/cf7550f68f339bf1d4f9b045b264c74c21ec93f7))
* enhance form submission handling with spinner support for file uploads ([fbc1177](https://github.com/Anthony-JCG/Platform/commit/fbc11779a775c0867f476ae6dfc1b936b7c925e8))
* enhance hidden category access modal with additional user information and improved layout ([4370333](https://github.com/Anthony-JCG/Platform/commit/437033341e7af9e416da0ca59014dc04e380d8ab))
* enhance hidden category access modal with improved layout and state management ([ad9f806](https://github.com/Anthony-JCG/Platform/commit/ad9f806d78c88d1c74b40514143c7d17788b31bd))
* enhance hidden category access modal with improved search input and event handling ([d2c4462](https://github.com/Anthony-JCG/Platform/commit/d2c4462f3b4294ab742a599d1c39eba84086a3de))
* enhance image handling for iOS with preloading and optimized clipboard copying ([84196b0](https://github.com/Anthony-JCG/Platform/commit/84196b0f3ebb0831d463c97a3e9b43901149d74d))
* enhance incentive card layout and button functionality for improved user interaction ([1e02a66](https://github.com/Anthony-JCG/Platform/commit/1e02a66fda68d4eb46c024ae433f360e5ffcd475))
* enhance incentive card layout and improve favorite toggle functionality ([6c62e7e](https://github.com/Anthony-JCG/Platform/commit/6c62e7e2ec36144adafcc4379ead952a28fa0614))
* enhance incentive description handling by normalizing Quill payload and rendering HTML ([3997156](https://github.com/Anthony-JCG/Platform/commit/399715646c745bb74863775ca79f685000076280))
* enhance invited users and team displays with status indicators ([a9f2734](https://github.com/Anthony-JCG/Platform/commit/a9f27344177a014727b20308a3b426baf623e2d7))
* enhance landing blocks modal with event-driven initialization and state management ([80bcea3](https://github.com/Anthony-JCG/Platform/commit/80bcea3ebe54d3f7c9f154f8dfd994cdcbefe298))
* enhance landing page access control and improve form handling ([f9eccf0](https://github.com/Anthony-JCG/Platform/commit/f9eccf0cb2fa395c5c49c9840b00048a7d2abcaf))
* enhance landing page block management with Quill editor integration and improved AJAX handling for nested forms ([dbceecc](https://github.com/Anthony-JCG/Platform/commit/dbceecc5840d43e0ec7d82f4c3a77cffc27e4f50))
* enhance landing page block with updated banner image help text and introduce new landing hero banner styles ([e91b9ba](https://github.com/Anthony-JCG/Platform/commit/e91b9bacdbbda8afbe4ed360a3c382e99b62166e))
* enhance landing page components with new banner image support, footer visibility toggle, and video block management ([56c72c2](https://github.com/Anthony-JCG/Platform/commit/56c72c2f680c4523a3a28b8ba145dad16a7c1934))
* enhance landing page customization and improve form handling ([38a6e9c](https://github.com/Anthony-JCG/Platform/commit/38a6e9c1aac1b7bf0b9a8f2ead3f5ea310070f61))
* enhance landing page forms and AJAX handling with nested item management and icon selection ([c820a73](https://github.com/Anthony-JCG/Platform/commit/c820a73346b2e15711bfdeb5f414cff4197a72ce))
* enhance landing page forms and improve formset management ([6fc2b84](https://github.com/Anthony-JCG/Platform/commit/6fc2b84d4c9a09ed5e210546664636b3ba184623))
* enhance landing page layout and improve component styling ([ffad738](https://github.com/Anthony-JCG/Platform/commit/ffad7387900ec95f3b690a6b99eb5bc1fc04b16e))
* enhance loader behavior for iOS/Safari to prevent navigation blocking ([bdccc20](https://github.com/Anthony-JCG/Platform/commit/bdccc20bb9d1fef71df1f46deaf54a5b5fd3bd28))
* enhance membership status management with editable limits and custom state handling ([201d22c](https://github.com/Anthony-JCG/Platform/commit/201d22c34c9eb9d1b74a764dae9031fc7b03dcec))
* enhance modal behavior with body restoration control and reset functionality ([5c7a192](https://github.com/Anthony-JCG/Platform/commit/5c7a19217a954a86e022f6bec3b046ca5fbbf67d))
* enhance modal components with improved accessibility and data handling ([260d4f4](https://github.com/Anthony-JCG/Platform/commit/260d4f42db91ac25afee101b0b1c3c8e86b5c1de))
* enhance modal design with scrollable dialog and clean up CSS ([e07316b](https://github.com/Anthony-JCG/Platform/commit/e07316b022a16cbc53eb70693c6e32b70d46eb5c))
* enhance modal for leader pro copy with improved structure and user feedback ([34e5144](https://github.com/Anthony-JCG/Platform/commit/34e51447d4eeb61f25f0b6560f00114cdf6d9649))
* enhance modal handling for Quill integration with tooltip adjustments ([7b0eca1](https://github.com/Anthony-JCG/Platform/commit/7b0eca1ff5e523a69e07616abde2a715b013a055))
* enhance personal notification with incentive details and update redirect URL ([367d207](https://github.com/Anthony-JCG/Platform/commit/367d207923a920bcfdbcf6c2db3a7aa156ee4ab7))
* enhance pricing page access control for debugging environments ([b791ce7](https://github.com/Anthony-JCG/Platform/commit/b791ce7ca286d683c775a220c75daa4d2560d9ab))
* enhance Quill editor configuration and styling with new alignment options and improved paragraph spacing ([7dc6e86](https://github.com/Anthony-JCG/Platform/commit/7dc6e86e43277c90305eb85182f096868dfc47ce))
* enhance Quill integration by adding inline editors and improving payload normalization ([ebcf616](https://github.com/Anthony-JCG/Platform/commit/ebcf616722687760aa7d650dde356a100a6c1688))
* enhance resource link handling with default values for improved robustness ([205b284](https://github.com/Anthony-JCG/Platform/commit/205b28427d310c25f7c5da0804e19007ba25609c))
* enhance route progress bar with dynamic color tones based on completion percentage ([6fa4f3b](https://github.com/Anthony-JCG/Platform/commit/6fa4f3b6b10681fc8aa77d3be40a10cfa5e63536))
* enhance route step form handling with read-only mode and improved event management ([9706aa3](https://github.com/Anthony-JCG/Platform/commit/9706aa35cb3c35bd2b16aebf039c5c7559324d3b))
* enhance scheduled task modal functionality and improve custom message autofill behavior ([e86fdc0](https://github.com/Anthony-JCG/Platform/commit/e86fdc0b5f4ae5d8b11ffcba2c199c2c0dcb4064))
* enhance search results display with locked category indication and URL cleanup functionality ([70061da](https://github.com/Anthony-JCG/Platform/commit/70061daeceb8c564201ae50309af1262b0340370))
* enhance section and subsection progress tracking with visual indicators ([da0005d](https://github.com/Anthony-JCG/Platform/commit/da0005d91bd4a05425bbd311f877933f972537ba))
* enhance section and subsection templates with progress indicators and styling adjustments ([b10f3ad](https://github.com/Anthony-JCG/Platform/commit/b10f3adee6ea43fdb483ea7016ebb87fac479b20))
* enhance share preview functionality with dynamic metadata resolution ([3d6a633](https://github.com/Anthony-JCG/Platform/commit/3d6a633c6b16b7ad15d784f82a19879c933afd0b))
* enhance stream import logic by excluding already imported streams and own titles ([045a0d1](https://github.com/Anthony-JCG/Platform/commit/045a0d11d468ec5f4620d6795ad35786625d8190))
* enhance streaming functionality by refining field handling for derived and independent streams ([48d31bc](https://github.com/Anthony-JCG/Platform/commit/48d31bc64d2270593d992893b0778eecf2539f6c))
* enhance Stripe integration with subscription management updates and notifications ([ddeca38](https://github.com/Anthony-JCG/Platform/commit/ddeca38c92cecd21a2372f1bce5c91cff7a2ede7))
* enhance tag filtering functionality with improved selection and sorting ([2fb1527](https://github.com/Anthony-JCG/Platform/commit/2fb1527917520d183d6e3c31f8e975d03b359f14))
* enhance training video modal and subsection layout with improved styling and dynamic video handling ([f3cf3ce](https://github.com/Anthony-JCG/Platform/commit/f3cf3ce9d90cb92798a3975a2f21ca3a44d36a64))
* enhance UI elements and improve view handling for basic users ([61bd296](https://github.com/Anthony-JCG/Platform/commit/61bd296c1a84b2078c2c279399ccf5d52d578489))
* enhance user answers button with conditional rendering and improve AJAX endpoints for user data loading ([a5c19fd](https://github.com/Anthony-JCG/Platform/commit/a5c19fd6e54b6c316b0c69599a4ca18efbe0f17a))
* enhance user downgrade handling and improve admin filters ([4caab64](https://github.com/Anthony-JCG/Platform/commit/4caab64aedf18f7738118d9ddcbb3e44d374d333))
* enhance user handling for downgraded leaders and improve notification logic ([8f1c13f](https://github.com/Anthony-JCG/Platform/commit/8f1c13f0e4acc95a146034129c667caf13cffaf2))
* enhance user retrieval and notification logic with level filtering ([d102a78](https://github.com/Anthony-JCG/Platform/commit/d102a78b01c6ca95405f6314d888c38a0a38aada))
* enhance username validation and provide user guidance in registration ([fb8cfc7](https://github.com/Anthony-JCG/Platform/commit/fb8cfc7c3549d0073cc8e156e7a2f7af6c3d28d5))
* enhance validation and item management in landing blocks with improved text and icon handling ([6a07e58](https://github.com/Anthony-JCG/Platform/commit/6a07e58bedf1e0d37c0b2102fb552daf2c9db84e))
* enhance video unlock logic in landing template view ([b594102](https://github.com/Anthony-JCG/Platform/commit/b594102f69c273c59c1ac168fe1bdf11e423e5a4))
* enhance video upload process with MD5 hashing and temporary file handling ([de3f8b9](https://github.com/Anthony-JCG/Platform/commit/de3f8b97cd72678984bb91b5aadd2ea96d033e4a))
* enhance waiting page layout and functionality with card design and tooltip improvements ([1b4dc7a](https://github.com/Anthony-JCG/Platform/commit/1b4dc7a2f79c2e3121208691852c370640f589d3))
* enhance welcome email formatting for new users ([7fbccfe](https://github.com/Anthony-JCG/Platform/commit/7fbccfe79e269942886b74ab87d2be0f05702f7a))
* enhance WhatsApp image sharing by improving clipboard functionality and handling WebP format ([1b93924](https://github.com/Anthony-JCG/Platform/commit/1b93924613146c7a32e216ea2c9253e71b3e14fd))
* enhance WhatsApp message for category completion with translations and additional context ([632bc51](https://github.com/Anthony-JCG/Platform/commit/632bc51f2c852a52b0085eb24dd4d30be3d0556c))
* enhance YouTube URL extraction to support shorts and improve regex patterns ([d7c08cc](https://github.com/Anthony-JCG/Platform/commit/d7c08cc8cec887529d33ee45c1bcd3062c206055))
* ensure distinct counting of subsections in category completion calculations ([1e90a21](https://github.com/Anthony-JCG/Platform/commit/1e90a21ded2ecb74e4ac6bec4beed4f330119b41))
* ensure distinct incentives for FIRST_LEADER_PRO user in query ([698c155](https://github.com/Anthony-JCG/Platform/commit/698c1554ab64711f25c9beb20e22903535eb2ff2))
* filter category training duplication based on user role ([dc59581](https://github.com/Anthony-JCG/Platform/commit/dc59581581fdccde09b06f63b5a8f12952c3f9e0))
* filter visible categories for user access in training model ([d1fc675](https://github.com/Anthony-JCG/Platform/commit/d1fc675150b08f2502a54b4e6a943808436b83bc))
* group form sections into cards with improved styling and layout ([46d9b73](https://github.com/Anthony-JCG/Platform/commit/46d9b733c395b8f63707f754e1c8acec34e0bf22))
* hide floating search button when a modal is open ([48ddd66](https://github.com/Anthony-JCG/Platform/commit/48ddd66e9c0d22c6f995bcbdaafca749a22ff4f7))
* ignore internal anchor links in page loader ([a15c09f](https://github.com/Anthony-JCG/Platform/commit/a15c09f65f3b3149e81a706225afadbcd22709e5))
* ignore internal anchor links in page loader ([54751bb](https://github.com/Anthony-JCG/Platform/commit/54751bb805af2da6b02183fbb4bbf7bac07300be))
* implement 7-day free trial system for new users upon completing initial training ([e5e7ad5](https://github.com/Anthony-JCG/Platform/commit/e5e7ad5f2b1acd7d789ae4617eba8c1e989022b8))
* implement active leader object copying during user leader upgrades ([a662a4a](https://github.com/Anthony-JCG/Platform/commit/a662a4a025ec4c1a546ef97c18c6fac27fb68909))
* implement AJAX form submission handler with error management and UX enhancements ([4fc0c77](https://github.com/Anthony-JCG/Platform/commit/4fc0c773bca1f34ddb90e397110c25dc5eb5984b))
* implement AJAX handling for task updates and improve modal functionality ([1fadda0](https://github.com/Anthony-JCG/Platform/commit/1fadda07cf1163b6cbed87cd901985030b5e4db8))
* implement anchor navigation for incentives and improve incentive tab structure ([51274f2](https://github.com/Anthony-JCG/Platform/commit/51274f26458b09a48ad69da52d3fe41361e7d2eb))
* implement automatic incentive creation if not provided and enhance task response with incentive ID ([0d1de64](https://github.com/Anthony-JCG/Platform/commit/0d1de6470b52d794c7ca0c409c9afae271735a0a))
* implement batch category completion calculation without content hydration ([aa70251](https://github.com/Anthony-JCG/Platform/commit/aa702519d943160cda532227c6eb11c3047c092b))
* implement button busy state helper for improved user feedback during async operations ([93e211f](https://github.com/Anthony-JCG/Platform/commit/93e211f1cb20ce66a79d0552475d42fe2cfc7631))
* implement cache invalidation for user progress and answers updates, and enhance user cache management ([2f51b68](https://github.com/Anthony-JCG/Platform/commit/2f51b68d20638c7003f9c07283e95a0261656f63))
* implement cascading delete for derived streams when unsharing existing objects ([4c22592](https://github.com/Anthony-JCG/Platform/commit/4c2259226a6bcce7fe40471c9e6a8b2b446d745c))
* implement centralized landing blocks management with save functionality ([7598d4d](https://github.com/Anthony-JCG/Platform/commit/7598d4d969637da36f37647c25e2882130e788be))
* implement challenge overview card with calendar and daily tasks display ([b90b8c6](https://github.com/Anthony-JCG/Platform/commit/b90b8c6052f66279191d20c3892de9bb90e9b5ca))
* implement change tracking for category, section, subsection, and input field saves ([3d611f4](https://github.com/Anthony-JCG/Platform/commit/3d611f44048449a24bc1d3484e08b7b6b8c09889))
* implement click prevention on downgraded elements and update warning messages for better user clarity ([a62b9b7](https://github.com/Anthony-JCG/Platform/commit/a62b9b7413886b6303f981f33b8a64759ba20094))
* implement custom membership status management with CRUD operations ([c6db312](https://github.com/Anthony-JCG/Platform/commit/c6db31287e444a3b98a13835150953d1133c4722))
* implement downgrade blocking logic for categories and update template for enhanced user experience ([b740637](https://github.com/Anthony-JCG/Platform/commit/b740637dff2f56e1f4680ce661926f1ea5c85081))
* implement downgrade handling for importable streams in waiting page ([f23f54b](https://github.com/Anthony-JCG/Platform/commit/f23f54be82cad5f26d5eda1f229fac641a6cdb36))
* implement downgrade handling for streaming objects and mark for deletion ([42da7b3](https://github.com/Anthony-JCG/Platform/commit/42da7b34b514bca1c9865fdb4911b4c56cd87a18))
* implement drag-and-drop functionality for landing blocks and items ([1fbb9da](https://github.com/Anthony-JCG/Platform/commit/1fbb9daf8f032c40f9c0d225ab066e0b94b45f48))
* implement email notifications for stream registration, reminders, and live start ([238f18e](https://github.com/Anthony-JCG/Platform/commit/238f18e82f0f4cc2081029ff31a8e75de3d3b3cd))
* implement favorite incentives functionality with toggle feature ([35f1138](https://github.com/Anthony-JCG/Platform/commit/35f1138a58742d8f232e9402ec5da74242a8ac11))
* implement floating search button with enhanced UI and accessibility features ([3269911](https://github.com/Anthony-JCG/Platform/commit/3269911eea09e13e755c2b36f4274716ece7ec11))
* implement global training stats modal and enhance data handling for user progress ([5e2be2a](https://github.com/Anthony-JCG/Platform/commit/5e2be2adba14464370d4e2539461ac7f7be4ca45))
* implement incentive card component with tabbed view for events and incentives ([c2d2b8e](https://github.com/Anthony-JCG/Platform/commit/c2d2b8eb374485d6abbdf974d6699492dcdc57c4))
* implement incentive card component with tabbed view for events and incentives ([cd78cb4](https://github.com/Anthony-JCG/Platform/commit/cd78cb4c5fcb313e2345f641e172f9230b7f395f))
* implement independent vertical scrolling for drag columns and update column counters ([1c83443](https://github.com/Anthony-JCG/Platform/commit/1c83443cc22716cae4444276aaebb1f717b4ce82))
* implement lazy loading for category content and update related templates ([6b5250b](https://github.com/Anthony-JCG/Platform/commit/6b5250bf173ae919133776468b43cac0e9e35b73))
* implement lazy loading for user descendants in my team view ([5657fb2](https://github.com/Anthony-JCG/Platform/commit/5657fb21320fdbbdc6438bef51e021e9bdcc07aa))
* implement local search functionality in hidden category access modal ([659c0cc](https://github.com/Anthony-JCG/Platform/commit/659c0cc958bd19de57c64823c7f7fa72cb53043e))
* implement modal for canceling free trial and update checkout forms based on trial status ([db222c6](https://github.com/Anthony-JCG/Platform/commit/db222c64519ce71feb828bb6a669fa05a411dd62))
* implement modals for managing pending invitations and refactor invitation validation logic ([1b30c05](https://github.com/Anthony-JCG/Platform/commit/1b30c05c4ff4a8e844d3c995f774af5024f740a9))
* implement nested formset management for learning, FAQs, and carousel blocks ([0323893](https://github.com/Anthony-JCG/Platform/commit/03238935a238f432cec4ae4da085ade2210779a7))
* implement page scroll locking for floating search functionality ([d87c4ee](https://github.com/Anthony-JCG/Platform/commit/d87c4eee9dfd98b959ac57ca26577586183d7b26))
* implement photo management in activity editing with FIFO rotation and preview modal ([6de1918](https://github.com/Anthony-JCG/Platform/commit/6de1918b3f0c78ead1207baefe5d4203fc31ac0c))
* implement route progress bar component and update user progress display ([f5ecdcf](https://github.com/Anthony-JCG/Platform/commit/f5ecdcf350e3d2f6f2192b23be3fee423ccaf64d))
* implement route step management with progress tracking and modal enhancements ([284eeca](https://github.com/Anthony-JCG/Platform/commit/284eecabc8ffaf1cff49d4b1da34585eae9fb20e))
* implement RouteStep model with Quill editor integration and update related templates ([670ccdf](https://github.com/Anthony-JCG/Platform/commit/670ccdfe9082be88ed595e66bda41867e9d8d350))
* implement section content loading via AJAX and enhance edit restrictions ([9274125](https://github.com/Anthony-JCG/Platform/commit/9274125ce977a87eb262947ffc0a17841b6ef353))
* implement share preview functionality with customizable meta tags ([20a6154](https://github.com/Anthony-JCG/Platform/commit/20a6154bfa7c6b4c935a2810f377c652a0eb4cfe))
* implement sorting and access management for hidden categories ([7e97744](https://github.com/Anthony-JCG/Platform/commit/7e97744ade97342bf78adb3a07a9bbb4dc10a997))
* implement Stripe integration for subscription management and add checkout success page ([5f680ac](https://github.com/Anthony-JCG/Platform/commit/5f680ac345eb58b6f6b14b475ba36afceba60aaf))
* implement subsection modal with dynamic field management and AJAX submission ([00ef65c](https://github.com/Anthony-JCG/Platform/commit/00ef65c68c7abf6e83aaa706215aef359e6c2166))
* implement tabbed interface for challenges hub and enhance personal tasks section ([fa684f8](https://github.com/Anthony-JCG/Platform/commit/fa684f87c929b2ffb15484cb207eca083e2b6a27))
* implement TypeIncentive management modal and save functionality ([3207a10](https://github.com/Anthony-JCG/Platform/commit/3207a10b05c84048838a9563d4370c71712c299f))
* implement user favorites feature for incentives and enhance incentive tab display ([2bcf14c](https://github.com/Anthony-JCG/Platform/commit/2bcf14c34bf17623c23629a955d9cc1cad15e62c))
* implement viewer registration and polling for stream viewers ([a7b92bb](https://github.com/Anthony-JCG/Platform/commit/a7b92bb963d3fc9be58fe26e033e847d575ca04a))
* implement viewer registration caching by IP for live streams ([298e56a](https://github.com/Anthony-JCG/Platform/commit/298e56af93f9cebcb3ec36aafd7a98b0c77146d1))
* improve autosave functionality for landing forms and integrate Quill editor support ([6ea06e7](https://github.com/Anthony-JCG/Platform/commit/6ea06e7e2633e8c7d4dd07c82d47899a5a6536e2))
* improve challenge overview card layout and functionality with calendar toggle updates ([030f608](https://github.com/Anthony-JCG/Platform/commit/030f6081fe1acf827277ebeac95cd8ad87295008))
* improve clipboard image copying functionality with error handling and return status ([93c3763](https://github.com/Anthony-JCG/Platform/commit/93c376354a16ac61a768c8ca91a845850a39d454))
* improve CSRF token handling and enhance form submission behavior ([29f071a](https://github.com/Anthony-JCG/Platform/commit/29f071aa2c83c4420f64b2716ef9b133874f16b0))
* improve delete confirmation handling and enhance button accessibility in landing page modals ([35c1e9f](https://github.com/Anthony-JCG/Platform/commit/35c1e9f3846e42a47de96fc0b66f08b3ab21b266))
* improve field ordering by handling pending fields without sections ([2413e84](https://github.com/Anthony-JCG/Platform/commit/2413e840e4a3c99a5e3c94347d782bf9309ab07e))
* improve file upload experience with loading overlay and error handling ([0ffedd4](https://github.com/Anthony-JCG/Platform/commit/0ffedd480c803ceb5710e00de43b2952ff3800df))
* improve landing form submission handling with enhanced button management and busy state support ([8be4395](https://github.com/Anthony-JCG/Platform/commit/8be4395cb5865bf4fe3778495fd8e9c165070167))
* improve landing page layout and enhance form handling ([1943542](https://github.com/Anthony-JCG/Platform/commit/1943542e7dfdf6818162b843502a540c319d1657))
* improve layout and accessibility of category and course card components ([151ad07](https://github.com/Anthony-JCG/Platform/commit/151ad07c9b777560511eb7c4a0206a228ec7b96b))
* improve loader functionality for all browsers and simplify iOS-specific logic ([3969eee](https://github.com/Anthony-JCG/Platform/commit/3969eeeeb4a1368bac75302f35b196fa31bd2dda))
* improve modal control by enhancing Quill input synchronization and restoring behavior ([63f5a0c](https://github.com/Anthony-JCG/Platform/commit/63f5a0c577ebd9f3074301998018f7804ec6929b))
* improve modal handling and add route step management features ([614e356](https://github.com/Anthony-JCG/Platform/commit/614e3567d3f8336779b27e63d1e64b1f38238825))
* improve notification texts with translation support and enhance alert messages for user downgrades ([29cdbe7](https://github.com/Anthony-JCG/Platform/commit/29cdbe733a7fd98cce002a1844f7c302f48de4b9))
* improve page loader behavior for iOS and optimize image copying to clipboard ([87f78b0](https://github.com/Anthony-JCG/Platform/commit/87f78b01119213bf8c57ec96143ba765b53575de))
* improve resource name handling by adding default value for better display ([b9bf16c](https://github.com/Anthony-JCG/Platform/commit/b9bf16cd060e12da27819b7f899f8f8912b6f25c))
* improve responsive design with adjusted font sizes and visibility for mobile elements ([29cefd0](https://github.com/Anthony-JCG/Platform/commit/29cefd0f556ef01a78baa69c6c13c7359450f2af))
* improve target value modal handling and add logging for task creation ([91c066f](https://github.com/Anthony-JCG/Platform/commit/91c066fc48f3b5c275fe3eedadd0a3d832c77df2))
* improve tooltip integration in form labels for enhanced user guidance ([917dd01](https://github.com/Anthony-JCG/Platform/commit/917dd0167b55354b5b5732ecb9b4be51b383d69c))
* include super block in landing page CSS for improved styling ([a85e64c](https://github.com/Anthony-JCG/Platform/commit/a85e64cfd84b1798bbd8acab790d711ffdc2ab44))
* integrate Quill editor for subsections and normalize legacy content handling ([eb8b1f2](https://github.com/Anthony-JCG/Platform/commit/eb8b1f23eb8dabb0750bd1481aaaca291ae04636))
* **landing:** add separator banner block with image support ([3709ced](https://github.com/Anthony-JCG/Platform/commit/3709ced5e4fb98a3ea72043b7528903422cee76e))
* **landing:** add video CTA label and WhatsApp prefill fields to block model ([d36b837](https://github.com/Anthony-JCG/Platform/commit/d36b8372ce9536d11bab501d0ec0c493a457799d))
* **landing:** gated video UX with disabled WhatsApp, no-seek, and 50% unlock ([f9bdf30](https://github.com/Anthony-JCG/Platform/commit/f9bdf307c4620cc651f734a74ae99624639521c8))
* **landing:** implement video CTA logic and update template ([85a994b](https://github.com/Anthony-JCG/Platform/commit/85a994bbb25585099e38ed35718e1367b3b1b1d9))
* **landing:** wire video gate context and CTA fields in forms and API ([8dfecb5](https://github.com/Anthony-JCG/Platform/commit/8dfecb53d9eed6bf1ae1dc2b921a3f431e3459ff))
* make membership and interest fields optional in forms ([26e067f](https://github.com/Anthony-JCG/Platform/commit/26e067fdb9bd8d843a8d67fd13db10a16c998e5d))
* normalize incentive description payload and update date field labels in migration ([9067ae8](https://github.com/Anthony-JCG/Platform/commit/9067ae8026c851c2db442d4ae499a7da8dd09bf3))
* normalize Quill payload handling and improve parsing logic across components ([13a0cdc](https://github.com/Anthony-JCG/Platform/commit/13a0cdceca78806439ef06e266e584421723ce0f))
* notify sponsor when user completes Phase 1 training and add email template ([d0ab2b4](https://github.com/Anthony-JCG/Platform/commit/d0ab2b4d6ef08b98dadf408e444384c2d0963f54))
* notify user and downline on new subsection creation if category is visible ([2502672](https://github.com/Anthony-JCG/Platform/commit/250267238c8c6db6164251f10a7225f2b1453ee9))
* optimize category completion calculation with SQL aggregations and exclude specific subsections ([b685c3a](https://github.com/Anthony-JCG/Platform/commit/b685c3aa6ecf2dccaf22dd4508af19e0318080a5))
* optimize child user data retrieval and sorting by route progress ([1781957](https://github.com/Anthony-JCG/Platform/commit/17819574d2d5f7ded3f4c67c4a176e0d53a91aa4))
* optimize downgrade alert logic to skip sponsor checks for existing leaders ([f1c3b91](https://github.com/Anthony-JCG/Platform/commit/f1c3b910163da0e108f02a9faf2457e937a12b01))
* optimize learning display logic in landing template ([cf35ad8](https://github.com/Anthony-JCG/Platform/commit/cf35ad8b2bb0411c058d51109e21fc2eb9c7cca4))
* optimize page loader for iOS with preload and improved visibility handling ([24c8de8](https://github.com/Anthony-JCG/Platform/commit/24c8de8c6476cbabe8c196603130f9140a14cc48))
* pass request to SimplifyNewContactForm for improved context handling ([526e37d](https://github.com/Anthony-JCG/Platform/commit/526e37da03e3e64b1469212f7ec04b129325e1c9))
* prepend URL prefix to landing page URL generation ([08cef38](https://github.com/Anthony-JCG/Platform/commit/08cef383bd1097542cdf38512f52cda40aef93de))
* reduce default TTL for notifications from 7 days to 3 days ([6ff94f9](https://github.com/Anthony-JCG/Platform/commit/6ff94f9d426667b334bed42a35209efbd03b84cf))
* reduce visual viewer count in Redis when viewers leave the stream ([00ec39e](https://github.com/Anthony-JCG/Platform/commit/00ec39eb3610cd6487432f940aa06d3661062607))
* refactor category title rendering and tooltip initialization logic ([27c8f23](https://github.com/Anthony-JCG/Platform/commit/27c8f2353c13d2d76ca4f350ba0bb16baf33267a))
* refactor component includes to use new pro-components structure for consistency ([6fb432f](https://github.com/Anthony-JCG/Platform/commit/6fb432f657fdb605cdd649998b0995c9e36a8786))
* refactor contact form and enhance message handling in landing templates ([5302281](https://github.com/Anthony-JCG/Platform/commit/530228108b6aeb29be96cb9a97d8bedffe05dcce))
* refactor favorite incentives handling to improve card movement logic ([0a8b1de](https://github.com/Anthony-JCG/Platform/commit/0a8b1de7a3d033f989d3dba50c611e404e867522))
* refactor form section handling and update phone field logic ([7b79118](https://github.com/Anthony-JCG/Platform/commit/7b79118c0459736c2472bdc97fcdc4becb423321))
* refactor form submission handling for subsection answers ([2ee54e9](https://github.com/Anthony-JCG/Platform/commit/2ee54e9ebbe00f968d194d05beb640a064fcb3e7))
* refactor get_effective_first_subsection function for improved type handling and clarity ([c164436](https://github.com/Anthony-JCG/Platform/commit/c164436527e9ed1f2f1cd968156b3bd90121a20a))
* refactor get_effective_first_subsection to use user parameter and improve logic for finding effective subsections ([a95529e](https://github.com/Anthony-JCG/Platform/commit/a95529e26af87df3234a7b65e2550887b568f592))
* refactor get_progress_challenge_user function and move it to utils module ([84139f4](https://github.com/Anthony-JCG/Platform/commit/84139f40f6c55cffd7b8f67f494d509a153da002))
* refactor get_training_stats to improve data structure and performance ([79e6ef3](https://github.com/Anthony-JCG/Platform/commit/79e6ef3ab409e3909deb9f01481286b27432958c))
* refactor incentive card layout for improved accessibility and user experience ([0a3019c](https://github.com/Anthony-JCG/Platform/commit/0a3019ca98604c0541b3f43ada463d0a6f8ee758))
* refactor incentive creation to use form validation and improve error handling ([c95c991](https://github.com/Anthony-JCG/Platform/commit/c95c991160a7b0e15d7aea0a52b7b0377a88207b))
* refactor landing block type selection and update button component ([6f56fc6](https://github.com/Anthony-JCG/Platform/commit/6f56fc6e7c660a3c332873fbd4d3fbd956d6c1e4))
* refactor landing page management and update URL structure ([bbccf0f](https://github.com/Anthony-JCG/Platform/commit/bbccf0f2a848cd8dc89f4684cd58c23cfb108127))
* refactor landing page save functionality to support manual saving and improve block management ([2adcf17](https://github.com/Anthony-JCG/Platform/commit/2adcf172ef85c98237c93b06cb011837f229d449))
* refactor modal handling and improve user action components ([ae6a926](https://github.com/Anthony-JCG/Platform/commit/ae6a926a35b88f6a7491817890cbf79c812ed4de))
* refactor modal handling and improve user action components ([a242816](https://github.com/Anthony-JCG/Platform/commit/a242816dea813fdbbc1ca6f6a80ab3f2b1f8e8ba))
* refactor modal import path and enhance resource URL handling with default values ([37aece4](https://github.com/Anthony-JCG/Platform/commit/37aece4cb3f44e7dd3f592138b35c48e182e3fd1))
* refactor modal includes to use new directory structure ([aae50f6](https://github.com/Anthony-JCG/Platform/commit/aae50f6c0bda5eb0e588438f25b693f75d3c3adf))
* refactor pricing section layout and improve plan selection logic ([4edbb9f](https://github.com/Anthony-JCG/Platform/commit/4edbb9f9cf241cda497c321a519d641914c0f4cb))
* refactor stream page layout for improved host information display ([bc4f65b](https://github.com/Anthony-JCG/Platform/commit/bc4f65b0ba8d6615c37237b73f5492ba66566495))
* refactor user route step retrieval to improve leader search logic ([91731d5](https://github.com/Anthony-JCG/Platform/commit/91731d51c0700ecdb136790a1b7cff51a191340d))
* refine favorite incentives handling in incentive tab display ([4b3d4c1](https://github.com/Anthony-JCG/Platform/commit/4b3d4c10e47f9967fef21dd986f883c2b4b5ff02))
* refine incentive card layout and update modal text for clarity and improved user experience ([cbd8f10](https://github.com/Anthony-JCG/Platform/commit/cbd8f10eee9469f291bc5dd8dd2ea3c766ddc517))
* refine landing page form handling and update field descriptions ([a6fcec4](https://github.com/Anthony-JCG/Platform/commit/a6fcec4739cedd9c3ef3807e638225c1684bbe3f))
* refine Quill modal styles by adjusting tooltip positioning and removing overflow settings ([fd9c393](https://github.com/Anthony-JCG/Platform/commit/fd9c393c12be72b84f405e478dbfffd6252d5ae1))
* remove commented-out link for pricing comparison in pricing page ([d380b98](https://github.com/Anthony-JCG/Platform/commit/d380b9827d905ef49cdba258ef73f10fadfcf3fe))
* remove database constraint for exclusive challenge or incentive presence ([c99065c](https://github.com/Anthony-JCG/Platform/commit/c99065cbc0b1780b5bb9973f733e4967f8c7bba0))
* remove debug logging from modal control and simplify Quill input synchronization ([13aab89](https://github.com/Anthony-JCG/Platform/commit/13aab89772067768dc7aec4be66a93a766c521c8))
* remove debug print statements and clean up response handling in views ([3743a97](https://github.com/Anthony-JCG/Platform/commit/3743a9743b4ac4ead1a6a1bb53bc5f5807497b9a))
* remove email contact button from team member display ([56b7bb5](https://github.com/Anthony-JCG/Platform/commit/56b7bb5fd2d993e280cb46f137ed60bb034267c9))
* remove labels from country and phone composite field for cleaner UI ([559e4a7](https://github.com/Anthony-JCG/Platform/commit/559e4a71a3f93e7adb037396f2e2f5e49c822741))
* remove labels from country and phone composite field for cleaner UI ([2b42373](https://github.com/Anthony-JCG/Platform/commit/2b42373d9444214ebb2f6ccf66e532fe7fce4618))
* remove landing page type field and update boolean field descriptions ([e7f3405](https://github.com/Anthony-JCG/Platform/commit/e7f34054fcf48d4670b81e54e85fe577925043d4))
* remove search input for 'my_resources' training mode ([d3e2334](https://github.com/Anthony-JCG/Platform/commit/d3e2334a7ea186fbcb0e86a9b1d7e3bb29fe8a60))
* remove unnecessary console logs from incentive task handling ([46983e7](https://github.com/Anthony-JCG/Platform/commit/46983e72d1fb4bef5a20d961ba5f654f7e6f2212))
* remove unused admin classes and Pro Builder endpoints ([be02a55](https://github.com/Anthony-JCG/Platform/commit/be02a55e55f8a400ad47b12fc3666b56a8757240))
* remove unused contact movement logic after membership status deletion ([9ea8d58](https://github.com/Anthony-JCG/Platform/commit/9ea8d5894ae3b202fa50f6808b1dddbc6b6c76a5))
* remove unused cycle contact movement logic from membership status management ([2c8371a](https://github.com/Anthony-JCG/Platform/commit/2c8371a69de9c53d6ccf06169a4f460305f6d68f))
* remove unused Subsection references from downgrade handling ([a2018de](https://github.com/Anthony-JCG/Platform/commit/a2018deb394a0dc87112f89fd381e838ac547bb7))
* rename course card component to section and update references in views and templates ([0414c32](https://github.com/Anthony-JCG/Platform/commit/0414c32f1ad1b15ff44afc14bb51f0358c82b544))
* rename function for clarity and improve user retrieval logic in subtree ([f819476](https://github.com/Anthony-JCG/Platform/commit/f819476aecbee52ba4a440da6c190fecf0472885))
* rename notification function for clarity and update references in the codebase ([57d3e56](https://github.com/Anthony-JCG/Platform/commit/57d3e567ff29eac8f689f41314af9ecf9d8c8484))
* rename search_styles.css to global_search.css and update reference in base.html ([3e0f8e5](https://github.com/Anthony-JCG/Platform/commit/3e0f8e57582847dc882c940a89bba8ea50948458))
* reorganize form fields with data section attributes for improved structure ([5c4d684](https://github.com/Anthony-JCG/Platform/commit/5c4d6848b3930823f0454c48eca6b9e7d993a7a2))
* replace back-to-top link with a floating search button for improved accessibility ([ee523e8](https://github.com/Anthony-JCG/Platform/commit/ee523e8225d4e53ff30cb628a27bf7371ac894e9))
* replace fetch with csrfHelpers.fetchWithCsrf for submitting subsection answers ([b49c77a](https://github.com/Anthony-JCG/Platform/commit/b49c77ad9811728fe3c229a501b6d72a293e2313))
* replace icons with SVGs for improved scalability and styling in subsection and training course formations ([465a71a](https://github.com/Anthony-JCG/Platform/commit/465a71a584dc39ed9e14a07095144571561faecd))
* replace manual CSRF token handling with csrfHelpers.fetchWithCsrf in stream-page.js ([9f6c9df](https://github.com/Anthony-JCG/Platform/commit/9f6c9dff01bcb7451039442e9eb6a0d50fb00c72))
* replace text field with QuillField in subsection model for rich text support ([459a817](https://github.com/Anthony-JCG/Platform/commit/459a817ec433cdc91dc31cf89dc3c56fd7cc8559))
* restrict drag-and-drop reordering to leaders and update related messaging ([7bf6195](https://github.com/Anthony-JCG/Platform/commit/7bf61951ff57879b4af6d57ffe0c72747d403036))
* restrict edit and delete options to category owner in category and section views ([3165e0a](https://github.com/Anthony-JCG/Platform/commit/3165e0ac2fc6486e1684c7190d4cc296cc72e14e))
* save user contact after creating a new contact instance ([e04f927](https://github.com/Anthony-JCG/Platform/commit/e04f927dec2db408891d80b0ed6c98f213293cd8))
* set start and end time to None in stream handling ([b60a91e](https://github.com/Anthony-JCG/Platform/commit/b60a91e6c693f0cd02e3ff80f4a1555be10efcad))
* simplify card styling and improve layout for better readability ([554f1cd](https://github.com/Anthony-JCG/Platform/commit/554f1cd06af005c86ddda12d1445bb8f075a3edb))
* simplify cutoff date assignment for user registration ([a7e5119](https://github.com/Anthony-JCG/Platform/commit/a7e5119b241820a7821432e304ad29a4b30386ac))
* simplify downgrade state checks and enhance flag deletion logic for improved reliability ([9778780](https://github.com/Anthony-JCG/Platform/commit/9778780a6b70d9f5a062cfa8501c7ac6dd615689))
* simplify modal post page by removing unnecessary blocks and inputs ([62503a2](https://github.com/Anthony-JCG/Platform/commit/62503a2c1e9fded805947b2a7e9767d6d27b1713))
* simplify modal training video layout by removing fullscreen option and adjusting styling ([2b74380](https://github.com/Anthony-JCG/Platform/commit/2b74380de4cdde8aa17ea99f1c974fa240ad26ef))
* simplify UserLevelProfileAdmin fields and remove unnecessary field filtering for non-developers ([1c8ca00](https://github.com/Anthony-JCG/Platform/commit/1c8ca00cb2253865b78f7785093f7d374e7897d1))
* simplify VAPID public key processing in context processor ([bcf642e](https://github.com/Anthony-JCG/Platform/commit/bcf642e5227bb8d61e435cfcbcae9f05112dc4a0))
* streamline category, section, and subsection templates by removing conditional checks and simplifying data attributes ([80804cc](https://github.com/Anthony-JCG/Platform/commit/80804cc7c2c1c2887eb8f1da67a239f762a25578))
* streamline CSRF token handling by directly using fetchWithCsrf in multiple modules ([ba132d0](https://github.com/Anthony-JCG/Platform/commit/ba132d0773f621349aa6eabfc7db981a4303b5cf))
* streamline Quill widget management and enhance modal integration in landing page components ([21dcf69](https://github.com/Anthony-JCG/Platform/commit/21dcf69b5fbe14db65dba11abc2e576b00442d25))
* synchronize Quill description for AJAX submission and validate payload format ([88a9b23](https://github.com/Anthony-JCG/Platform/commit/88a9b2370f9326b5ad69be8d16ef352f42f04544))
* unify membership status management with save endpoint and UI updates ([599a48a](https://github.com/Anthony-JCG/Platform/commit/599a48af5818b6f366bc48f151af93ed8b0eb572))
* unregister Subsection model from admin interface for future reference ([c601d8a](https://github.com/Anthony-JCG/Platform/commit/c601d8ac64d8e2893fef198fd184ffbc42dbc7ed))
* update .gitignore to include .sql files and modify allowed hosts for deployment ([2d24fb8](https://github.com/Anthony-JCG/Platform/commit/2d24fb8cf8ec5c8554e808530fc080677fbfc949))
* update .gitignore to include AGENTS.md and correos.txt ([b63fea3](https://github.com/Anthony-JCG/Platform/commit/b63fea37283ec0519bdc8798be1ac33fb37992c4))
* update admin interface for CategoryTraining and Subsection models ([0f42b18](https://github.com/Anthony-JCG/Platform/commit/0f42b18813273927218ddc0e47213bd006d59866))
* update admin interface for CategoryTraining and Subsection models ([9cfe7b1](https://github.com/Anthony-JCG/Platform/commit/9cfe7b167a4da1244c819db6b518ec15189f39a2))
* update authentication pages to reflect invitation-only access and modify request modal text ([83069bd](https://github.com/Anthony-JCG/Platform/commit/83069bd2cdedb89bc396fd01ecce0e99dc7b8663))
* update button copy functionality with new anchor names and enhance scrolling behavior for collapsible elements ([1408307](https://github.com/Anthony-JCG/Platform/commit/1408307d2605ddff88e6379ae31d2adb8d43f748))
* update button copy URLs in category and subsection templates to use dynamic training URLs ([1bbe381](https://github.com/Anthony-JCG/Platform/commit/1bbe381debb93271c8d89833001d9efcc31cb40b))
* update button copy URLs in category and subsection templates to use dynamic training URLs ([92c8733](https://github.com/Anthony-JCG/Platform/commit/92c873361c01928daa1e4f7ae2dfc04ee2fb8494))
* update button includes to toggle Bootstrap usage for improved compatibility ([7d4c833](https://github.com/Anthony-JCG/Platform/commit/7d4c833978b6c8e1d3ac40a16110aa43ae3c371b))
* update capabilities and context processor to include 'waiting_page' in restricted routes and modify option for 'waiting_page' ([fa6cfdb](https://github.com/Anthony-JCG/Platform/commit/fa6cfdb2af4d5a838aa0ecc8ae146bd921de5cc3))
* update card challenge titles to use translation function and adjust calendar toggle label ([6fb4b4f](https://github.com/Anthony-JCG/Platform/commit/6fb4b4f864dce8262124e535f1bb0696c3e3f99f))
* update carousel item selectors and enhance debugging in landing blocks management ([ec2bbcc](https://github.com/Anthony-JCG/Platform/commit/ec2bbcc0c849bc9601b777e2d98a1f90443f3d64))
* update category and subsection components for improved button layout and accessibility ([aa9c291](https://github.com/Anthony-JCG/Platform/commit/aa9c2916f1457787bebe574b1e89478d452e68ab))
* update challenge management views and templates for improved user experience ([2ee8220](https://github.com/Anthony-JCG/Platform/commit/2ee82207827d8ad8d48344b86bd6ef0740ad6aa7))
* update contact card to display tags as tooltips and add new tooltip template ([bfd0f26](https://github.com/Anthony-JCG/Platform/commit/bfd0f26e7ea148de3b5ee11a40c4d31f6e024603))
* update contact model and forms to replace LinkedIn with TikTok and add interest field ([a2adea2](https://github.com/Anthony-JCG/Platform/commit/a2adea234e2634c174d06a71ab22547eab6e496c))
* update cookie handling for production and test environments ([16d7b17](https://github.com/Anthony-JCG/Platform/commit/16d7b17ceff650c3e9d2b48236c3ec9b4f02948f))
* update created-by section styling for improved visibility and layout ([7fd274e](https://github.com/Anthony-JCG/Platform/commit/7fd274e5ab3da910051565f61fcf929ea367319f))
* update CSRF token retrieval method for improved security and consistency ([61ca62a](https://github.com/Anthony-JCG/Platform/commit/61ca62a536dffc380a9c294f203016a1e8333b88))
* update CSRF token retrieval method for improved security and consistency ([3b687a2](https://github.com/Anthony-JCG/Platform/commit/3b687a2e0621e235ee3ee5fb017486b920f4fa1c))
* update default user level assignment to 'PRO' and add ordering to Level model ([66c49f6](https://github.com/Anthony-JCG/Platform/commit/66c49f6d058bc9735fa04bb206e44335b0c3e283))
* update domain references to use settings.DEFAULT_DOMAIN for consistency ([b53f962](https://github.com/Anthony-JCG/Platform/commit/b53f9629a3aa431d371770f40356475b6fc26565))
* update downgrade handling to use grace period hours and restore trial end logic ([72a5bc9](https://github.com/Anthony-JCG/Platform/commit/72a5bc9f543eafa7dc85890e04b6b1a28da53568))
* update email host password for improved security ([b77195d](https://github.com/Anthony-JCG/Platform/commit/b77195d0c99bd43b36e6c1046755e6eb81ad0380))
* update email host to correct domain for SMTP configuration ([70ce67c](https://github.com/Anthony-JCG/Platform/commit/70ce67cfb4f6a70b08617bbf327eaaf159abbcfb))
* update error messages for incentive creation and validation to improve user clarity ([368c9ce](https://github.com/Anthony-JCG/Platform/commit/368c9ce900b1cd09746151d9e080c5c243856066))
* update favorite button styling and reposition in incentive card ([256000a](https://github.com/Anthony-JCG/Platform/commit/256000abc02abdf60915d1540f87ddc9964a5f9a))
* update favorite incentives handling to restrict functionality based on user subscription status ([8d0f908](https://github.com/Anthony-JCG/Platform/commit/8d0f908a90840bef991c2cb491481f4da151c07b))
* update favorite incentives handling to restrict functionality based on user subscription status ([e32b628](https://github.com/Anthony-JCG/Platform/commit/e32b628a44c995bca424531ff32be5236ccd76f2))
* update field labels for clarity and enhance modal styling in monthly stats ([d949268](https://github.com/Anthony-JCG/Platform/commit/d9492687468d35384462335d552e6de9dab3c31d))
* update file link rendering to use SVG icons for improved visual consistency ([b86d1e9](https://github.com/Anthony-JCG/Platform/commit/b86d1e90088e193dbdf661b39aa237e55f82c783))
* update file link rendering to use SVG icons for improved visual consistency ([5d15448](https://github.com/Anthony-JCG/Platform/commit/5d154482bd74d439ff98a7f5c634e299d9a626d9))
* update filter modal to improve layout and accessibility with enhanced heading styles and floating labels ([2512711](https://github.com/Anthony-JCG/Platform/commit/251271171fe755624794c3e62d412cd7f440ed0d))
* update floating search backdrop opacity and simplify snippet extraction logic ([f2d1f00](https://github.com/Anthony-JCG/Platform/commit/f2d1f001570ea56fa1247f4c6d3a99f77c2ffa68))
* update floating search backdrop visibility condition for authenticated users ([7711fc4](https://github.com/Anthony-JCG/Platform/commit/7711fc48fd6aa2fba000786aedcce4dc4c0c1f1e))
* update floating search backdrop visibility condition for onboarding path ([71f0daf](https://github.com/Anthony-JCG/Platform/commit/71f0daff77ec95d9c973db91aaf499ba341ded9e))
* update floating search styles for improved layout and scroll behavior ([3e976aa](https://github.com/Anthony-JCG/Platform/commit/3e976aaa5d7b7164264ae57ff6718a8f38eb8a32))
* update floating search styles to improve responsiveness and interaction ([71ad51f](https://github.com/Anthony-JCG/Platform/commit/71ad51f91f59ab31b8b4a00cc4883eb7e80161cf))
* update form field attributes to set objectives as read-only for existing instances ([ce5cbd9](https://github.com/Anthony-JCG/Platform/commit/ce5cbd9a418622307a51434f6ca50d363e4fdc6e))
* update form validation and error handling for streaming registration ([f457a97](https://github.com/Anthony-JCG/Platform/commit/f457a97073678cef241035129de7262f8e58373c))
* update global search visibility based on user authentication and request path ([30c0e1c](https://github.com/Anthony-JCG/Platform/commit/30c0e1c43608f534923946a016757e5d8e1b62dd))
* update gunicorn service configuration and enhance .gitignore for additional file types ([e89daa5](https://github.com/Anthony-JCG/Platform/commit/e89daa54a981fafaf519aa4b7ba3fc9135fc27c8))
* update gunicorn service configuration to remove loglevel setting ([2a7bb43](https://github.com/Anthony-JCG/Platform/commit/2a7bb432fe4a632670845e0b4abef10fa62c5a12))
* update hidden category access logic and improve user display in training modal ([523a7e3](https://github.com/Anthony-JCG/Platform/commit/523a7e3cbdc7b4902fdca744f0f017486ec249c4))
* update icon list choices for improved visual representation ([7b88f62](https://github.com/Anthony-JCG/Platform/commit/7b88f62de9dcafb1b66cc55e09d14681b21e5baf))
* update incentive card layout and styling for improved responsiveness ([4cd524d](https://github.com/Anthony-JCG/Platform/commit/4cd524d9986d4b637283681a263d0b246f1f64e1))
* update incentive description field to use QuillField and adjust imports for payload normalization ([a72280d](https://github.com/Anthony-JCG/Platform/commit/a72280defa76b4348d96c28c0e893458d5dbf2cc))
* update incentive IDs for accordion elements and enhance notification redirect logic ([f2407fb](https://github.com/Anthony-JCG/Platform/commit/f2407fb75516b7a2df1d7eb9ea67ae5a446a8224))
* update invited users display to include contact link for users with contact ID ([1084d52](https://github.com/Anthony-JCG/Platform/commit/1084d520a8b8204bde93d983469de9f838545f2f))
* update key points handling in stream model and template ([5fad262](https://github.com/Anthony-JCG/Platform/commit/5fad262e024044e3ada36ba62a1e0988acb240d3))
* update landing page form handling and improve content management ([0692f11](https://github.com/Anthony-JCG/Platform/commit/0692f11976f89be92f7212202de3dc2881b2db78))
* update landing page learning item model to enhance image and text field configurations with improved help text ([e5ca3e7](https://github.com/Anthony-JCG/Platform/commit/e5ca3e7a50af4b13f4c7305689a61ea8d12b3d6c))
* update landing page URL structure and improve access control ([041b3db](https://github.com/Anthony-JCG/Platform/commit/041b3dbeca8dd7dad6bc5fc88b3585ee18d86b2e))
* update leader pro category retrieval to use single creator reference ([4c862f2](https://github.com/Anthony-JCG/Platform/commit/4c862f227b6c46d990bdcfd2abc62b91b7b1d99b))
* update Level model by removing name field and adding Stripe ID fields ([47da4ba](https://github.com/Anthony-JCG/Platform/commit/47da4ba80cf1235d379bbe2416e04bf14544d483))
* update level_top parameter to be optional in relevant functions and enhance incentive visibility for FIRST_LEADER_PRO ([b54d098](https://github.com/Anthony-JCG/Platform/commit/b54d09895dbce0ebe219d2613d7af70fdd7d3baf))
* update loader functionality for iOS Safari to ensure synchronous display before navigation ([62a83e2](https://github.com/Anthony-JCG/Platform/commit/62a83e29ea0aa72ac1fc7172a1f8610b304d7bc7))
* update logging level from error to info for task updates ([fad0ad6](https://github.com/Anthony-JCG/Platform/commit/fad0ad6403b880d26e2195139566778f34602b51))
* update logo image format in password reset templates ([494cd29](https://github.com/Anthony-JCG/Platform/commit/494cd29b723229a333e308d1cf753b2b92058d9b))
* update membership status labels for improved clarity in Spanish ([b2aaa3f](https://github.com/Anthony-JCG/Platform/commit/b2aaa3f925e7194b28e79afbcdf230a55d60e20a))
* update modal and pricing page for 'Leader Pro' plan requests with new messaging and email address ([2e2ad2e](https://github.com/Anthony-JCG/Platform/commit/2e2ad2eb81573788b5fc5249232b2486d1809e6b))
* update modal targets based on user subscription status in monthly stats ([a6b0d9f](https://github.com/Anthony-JCG/Platform/commit/a6b0d9fea19ea7e874a2257c0d5b0a0d5e7753e2))
* update monthly acquisition stats fields and remove task constraint ([771524b](https://github.com/Anthony-JCG/Platform/commit/771524b7229604bdef8d7e3e6af75fab295a3d27))
* update notification message for subscription cancellation and ensure URL is set correctly ([a290129](https://github.com/Anthony-JCG/Platform/commit/a2901292709ab71c6194f6a2ad5bda00800c2642))
* update notification templates to include dynamic incentive titles in user notifications ([2493cf9](https://github.com/Anthony-JCG/Platform/commit/2493cf917c014f5ce11191cbd92620568a5d67b1))
* update options for user interface in context processor ([bf852bc](https://github.com/Anthony-JCG/Platform/commit/bf852bc5a48ff4ce9ccd7a4ac293a965f1a65232))
* update ordering of incentives by start date in model and view ([d942ae5](https://github.com/Anthony-JCG/Platform/commit/d942ae5fcad531e9248f8ca1a859f01c9369d617))
* update personal information terminology to 'Perfil' ([d5559da](https://github.com/Anthony-JCG/Platform/commit/d5559da7e06ef20849aa529772804161ff707e30))
* update pricing page access control and add Stripe customer ID field in admin ([6f52b36](https://github.com/Anthony-JCG/Platform/commit/6f52b3656a66d46fef4549abb41d9add8ae504d5))
* update pricing page to use mailto for 'Leader Pro' plan requests and adjust form handling ([8c0c87d](https://github.com/Anthony-JCG/Platform/commit/8c0c87d3bd09440261193da97c369db3e5b0dc7d))
* update pro content and add WhatsApp link capabilities ([4fcc197](https://github.com/Anthony-JCG/Platform/commit/4fcc197a578e07b3892ee3663e1fe615e53c25e0))
* update Pro features section with tutorial and files links ([2eda34a](https://github.com/Anthony-JCG/Platform/commit/2eda34ab40a7cf9b79c22b2361eab442db72a406))
* update resource name input handling in subsection template ([738029e](https://github.com/Anthony-JCG/Platform/commit/738029e187bbfb69a3fd97ceeab0cb27a3635aa0))
* update scheduled tasks data handling to improve subscription check logic ([bfb425f](https://github.com/Anthony-JCG/Platform/commit/bfb425f19f952571fbb92e2167ee2795b86f81ef))
* update section title rendering and adjust styling for locked categories ([16d88b7](https://github.com/Anthony-JCG/Platform/commit/16d88b7ac6bd0605da6a93074055a869a7a293bb))
* update session and CSRF cookie handling for test environment ([25e812a](https://github.com/Anthony-JCG/Platform/commit/25e812ac958bf5f83164b89fa13bcec4660c5c56))
* update session and CSRF cookie handling for test environment ([f95b0ad](https://github.com/Anthony-JCG/Platform/commit/f95b0ad1df59eebd195fa7c5612900edb8acb5c9))
* update settings to use DEFAULT_DOMAIN for allowed hosts and email configuration ([c19e294](https://github.com/Anthony-JCG/Platform/commit/c19e29481a50ae8a027cbfcc7798c4e34dffdca5))
* update share preview URL generation to use pane name string variable ([a334180](https://github.com/Anthony-JCG/Platform/commit/a3341802c1584eab5ee69a023fd5fa5c539b53cd))
* update soon condition for landing page access control ([bd9efdb](https://github.com/Anthony-JCG/Platform/commit/bd9efdbb57ce1472a9f587ab550440b32f6381a6))
* update streaming form fields for better organization and improve recurrence type label ([ce963d1](https://github.com/Anthony-JCG/Platform/commit/ce963d16c98039b815343445b031bf58245f0098))
* update streaming modal permissions and improve user feedback for basic plan ([5400290](https://github.com/Anthony-JCG/Platform/commit/5400290f81017e66adb76d5906110a45c424b179))
* update StreamingForm fields to exclude specific fields and include is_active ([345113f](https://github.com/Anthony-JCG/Platform/commit/345113f414c4d074f8a356d156c5b5e7d8591fa2))
* update subscription terminology and enhance pricing page layout ([afe7cf5](https://github.com/Anthony-JCG/Platform/commit/afe7cf51d6b81f634483dbabf7e9e6efb7e8e0ab))
* update subscription terminology and enhance pricing page layout ([69f048d](https://github.com/Anthony-JCG/Platform/commit/69f048dcbaa91e1c18770b664e58585aa23d8801))
* update subscription terminology and enhance pricing page layout ([c4957b8](https://github.com/Anthony-JCG/Platform/commit/c4957b85176e3695afd3349c96f24fb822561982))
* update top sponsor logic to use the user as the top for leader actions ([8fd9659](https://github.com/Anthony-JCG/Platform/commit/8fd96591b07463dffc69448dcd2b47b527ad4573))
* update training course formations to restrict edit access based on user ID ([327415d](https://github.com/Anthony-JCG/Platform/commit/327415de29249b55dcee7acdd05d57313d78f33d))
* update translation for external resource label to enhance user understanding ([ca5d011](https://github.com/Anthony-JCG/Platform/commit/ca5d0112cad299818fd7ee59891acc5a28adbf1c))
* update TypeIncentive form to remove empty label and set required field ([f02c593](https://github.com/Anthony-JCG/Platform/commit/f02c593b865c438ffdc3ba75194fffe3ad23bd4b))
* update URL_PREFIX configuration to support test environment ([8e56b53](https://github.com/Anthony-JCG/Platform/commit/8e56b53acaffc437610b26d8ef3c24f6a207c25b))
* update user invitation and inactive users display with improved UI elements ([3a8ee8d](https://github.com/Anthony-JCG/Platform/commit/3a8ee8d8ebdc2fb9c18b41f04d7d63a4d30147c0))
* update user invitation and inactive users display with improved UI elements ([41d1bf2](https://github.com/Anthony-JCG/Platform/commit/41d1bf2f44f509b98999b123091c15d709b7468d))
* update verbose names for client and distributor fields to improve clarity ([69b6be9](https://github.com/Anthony-JCG/Platform/commit/69b6be91c8465a94e81990743c68ef54f16d2e9b))
* update waiting page instructions and correct WhatsApp message translation ([e7ace4c](https://github.com/Anthony-JCG/Platform/commit/e7ace4ca32c79adeee524116143680a3baf892bc))
* update WhatsApp button to use data attribute and improve image copying error handling ([749bb9f](https://github.com/Anthony-JCG/Platform/commit/749bb9f25fa0b56b5c1f0160fad445c08c1fbd3c))
* update WhatsApp setup to close modal and redirect synchronously for improved iOS compatibility ([9a0f692](https://github.com/Anthony-JCG/Platform/commit/9a0f6925a317d8108a73c9f33d22d09b372035c2))
* use UserLevelProfile model for fix bug ([3c2f7a0](https://github.com/Anthony-JCG/Platform/commit/3c2f7a00ebd5513b9fa7e1ceecec3080c670ce7e))


### Bug Fixes

* conditionally render username in created-by template based on debug mode ([0ff8d22](https://github.com/Anthony-JCG/Platform/commit/0ff8d22ef49d98d0bca1ca44ee1f0fc5c429c0de))
* correct render function call in waiting_page view to include request parameter ([ec2d9c6](https://github.com/Anthony-JCG/Platform/commit/ec2d9c6910bdc0d2e039fde2d9e5fd9cf344de56))
* disable blocked predefined messages in WhatsApp modal ([551bcac](https://github.com/Anthony-JCG/Platform/commit/551bcacd2eddd5aeaa2c3616473e8d375641aef1))
* enhance task completion handling and update tooltip functionality ([5876e9f](https://github.com/Anthony-JCG/Platform/commit/5876e9f70b6f3f3ccbebe1f17d9efc7e23ff0cf0))
* reduce task creation limits in capabilities configuration ([8087a9b](https://github.com/Anthony-JCG/Platform/commit/8087a9b6e658a7b7ebf18d06efdfc1b7f2ad401a))
* update text wrapping for activity notes in card contact view ([d30a8cf](https://github.com/Anthony-JCG/Platform/commit/d30a8cfdf36f19c3c81113af23f34528bb599705))
* update welcome user template to improve layout and readability ([22a4769](https://github.com/Anthony-JCG/Platform/commit/22a476905c1520d8f085b38f07ce17635b4d66f2))


### Code Refactoring

* **context_processor:** update user access logic for production ([5bf996a](https://github.com/Anthony-JCG/Platform/commit/5bf996a7d782bc56a84a327302a1a981690967d0))
* **context_processor:** update user access logic for production ([36169de](https://github.com/Anthony-JCG/Platform/commit/36169ded055892b400936c75c88becd26a2a51fb))
* **landing:** add gift email notification and update email content ([4b1620d](https://github.com/Anthony-JCG/Platform/commit/4b1620d8fcf4358dcaa8bf413782c271255541a4))
* **landing:** make video CTA and WhatsApp fields optional ([9ca9c68](https://github.com/Anthony-JCG/Platform/commit/9ca9c686eca8efff681b93f4d0cccad83ed4c68c))
* **landing:** update video unlock logic and session handling ([e9682ed](https://github.com/Anthony-JCG/Platform/commit/e9682ed71b854d16191c0291e95cfa984d06cbf3))
