# A3 semantic annotation validation sample

This deterministic, time-stratified blind-review sample contains 40 real person-quarter bundles. Founder/control outcome labels and matched-group identifiers are intentionally withheld.

## Bundle 01: `adelyser` — `2021-04-01`

Items in bundle: 5

### Bundle text

<pre>item_index: 1
created_at: 2021-05-18 04:56:38
event_type: PullRequestEvent
repo_name: kageurufu/Marlin-CR30
title: 2.0.8.1
body:
### Description

Merged MarlinFirmware 2.0.8.1.

### Requirements

No specific requirements needed.

### Benefits

Pulls in the latest Marlin release features.
[Marlin 2.0.8.1 release info](https://github.com/MarlinFirmware/Marlin/releases/tag/2.0.8.1)

### Configurations

Configuration files updated in the PR.

### Related Issues
</pre>

<pre>item_index: 2
created_at: 2021-05-16 14:50:27
event_type: IssueCommentEvent
repo_name: pyro2927/SouthwestCheckin
title: Too many redirects for openflights.org 
body:
Looks like openflights.org is back online.</pre>

<pre>item_index: 3
created_at: 2021-04-20 05:39:18
event_type: PullRequestEvent
repo_name: kageurufu/Marlin-CR30
title: Bugfix 2.0.x cr30
body:
### Requirements

* Filling out this template is required. Pull Requests without a clear description may be closed at the maintainers&#x27; discretion.

### Description

&lt;!--

- Disable Serial port 2, it conflicts with the LCD pins.
- Fixed a BL Touch pin definition.
- Added UART pins for TMC drivers when used.
- Defined and enabled control of the LED connector. It&#x27;s a simple ON/OFF.
- Enabled PID Auto-tuning in the menu.

Ultra-silent idle state from the next two.....
- Enabled FAN2 connector to auto control the extruder fan. This automatically turns the extruder fan on/off at 50C.
- Enabled FAN3 connector to auto control the driver cooling fan. This automatically turns on the driver cooling fan when the steppers are activated, and shuts off 5 minutes after the steppers have stopped moving.

--&gt;

### Benefits

Many new useful features.

1.  Ability to auto-tune from the menu.
2.  Ultra silent idle state.
3.  LED light control.
4.  TMC uart control if soldered up  on the board.

### Configurations

- Included in the PR.

### Related Issues

&lt;!-- Whether this fixes a bug or fulfills a feature request, please list any related Issues here. --&gt;
</pre>

<pre>item_index: 4
created_at: 2021-04-16 03:57:48
event_type: PullRequestEvent
repo_name: adelyser/Marlin-CR30
title: Disable serial2, fix bltouch pin
body:
### Description

Disable SERIAL2 as the pins it uses conflict with the LCD serial pins.
Fix a BL Touch pin that is defined incorrectly.

### Benefits

Small minor issues found during testing, may or may not cause LCD Issues.
BL Touch can be used with the pin fix.

### Configurations

Part of the PR changes.

### Related Issues

None that I know of.</pre>

<pre>item_index: 5
created_at: 2021-04-16 03:56:10
event_type: PullRequestEvent
repo_name: adelyser/Marlin-CR30
title: Disable serial2, fix bltouch pin
body:
### Description

Disable SERIAL2 as the pins it uses conflict with the LCD serial pins.
Fix a BL Touch pin that is defined incorrectly.

### Benefits

Small minor issues found during testing, may or may not cause LCD Issues.
BL Touch can be used with the pin fix.

### Configurations

Part of the PR changes.

### Related Issues

None that I know of.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;hardware&quot;,
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;description&quot;: &quot;Maintaining and updating Marlin firmware configurations for the CR-30 3D printer, including merging upstream releases and fixing pin definitions.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 02: `andreasjansson` — `2014-07-01`

Items in bundle: 3

### Bundle text

<pre>item_index: 1
created_at: 2014-09-29 15:27:43
event_type: PullRequestEvent
repo_name: andreasjansson/envtpl
title: Enable template includes ({% include &#x27;foo.txt&#x27; %}.
body:
None</pre>

<pre>item_index: 2
created_at: 2014-09-29 05:32:03
event_type: PullRequestReviewCommentEvent
repo_name: andreasjansson/envtpl
title: Enable template includes ({% include &#x27;foo.txt&#x27; %}.
body:
The original idea of the `render` function was to have an interface to envtpl that you could just pass a string and some variables and get the same result as you would on the command line. I&#x27;m not sure anyone used `render` in that way, other than me in some old project. I can&#x27;t think of a nicer way of allowing includes right now, so let&#x27;s just make `render` =&gt; `_render` so it at least isn&#x27;t exposed in the API.</pre>

<pre>item_index: 3
created_at: 2014-09-18 15:16:17
event_type: PullRequestEvent
repo_name: andreasjansson/envtpl
title: Tox
body:
I tweaked the test to be python 3.4 compatible and added a configuration file for tox (```pip install tox```), which will run tests for you in fresh virtualenvs in different versions of Python. This should address @andreasjansson &#x27;s question in #3 as to whether commit 20a12c5 fixes python3 support. Answer: almost (another PR forthcoming).</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;description&quot;: &quot;Continuing development of envtpl, a Python templating CLI tool, adding template includes, adjusting API surface, and adding tox-based cross-version testing.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      2,
      3
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2,
      3
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      2,
      3
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 03: `bfirsh` — `2016-07-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2016-09-30 14:21:18
event_type: IssueCommentEvent
repo_name: bfirsh/docker-api-reference
title: Better documentation for all of the attach options
body:
stream and logs are now better documented. Todo: making stdin work.</pre>

<pre>item_index: 2
created_at: 2016-09-29 19:29:49
event_type: PullRequestReviewCommentEvent
repo_name: docker/docker
title: add code 200 of network rm
body:
This should probably just be removed if the endpoint doesn&#x27;t return 204.</pre>

<pre>item_index: 3
created_at: 2016-09-29 19:23:04
event_type: IssuesEvent
repo_name: bfirsh/docker-api-reference
title: Document how hijacking works
body:
Multiplexing, upgrade headers, etc.</pre>

<pre>item_index: 4
created_at: 2016-09-29 11:43:39
event_type: IssueCommentEvent
repo_name: docker/docker
title: make remove network return 204
body:
Oh jeez, I didn&#x27;t realise the docs were wrong. I agree with you:

1) +100 fixing the docs immediately (including old versions which are wrong, if you feel like being comprehensive ;)
2) I think changing the status code should be versioned.</pre>

<pre>item_index: 5
created_at: 2016-09-28 16:08:17
event_type: IssueCommentEvent
repo_name: docker/docker
title: [Remote API] Creating a service with an invalid network returns 404 (should return 406)
body:
Thanks! However, 406 is normally used for content type issues, not request body issues. Admittedly, we do misuse it elsewhere in the API.

A plain old 400 would be more suitable. Or, if you wanted something more specific, perhaps [422](https://httpstatuses.com/422).</pre>

<pre>item_index: 6
created_at: 2016-09-28 15:59:06
event_type: IssueCommentEvent
repo_name: docker/docker
title: make remove network return 204
body:
Yeah, 200 is technically wrong, but it isn&#x27;t going to cause any trouble.

We may as well do an API version check, right? That way we can change it to 204 and it definitely won&#x27;t break anything.</pre>

<pre>item_index: 7
created_at: 2016-09-27 14:34:04
event_type: IssueCommentEvent
repo_name: dnephin/dobi
title: Add one line install to readme
body:
Ah, yeah. Perhaps it should clearly say &quot;for mac&quot;. That&#x27;d cover the 80% case, then.</pre>

<pre>item_index: 8
created_at: 2016-09-27 11:20:16
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Move BaseTestCase to BaseIntegrationTest
body:
@shin- Made a simpler version which just adds `timeout` to `from_env()`. :)</pre>

<pre>item_index: 9
created_at: 2016-09-27 10:43:49
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Move BaseTestCase to BaseIntegrationTest
body:
Hm, alright. `from_env()` should accept all kwargs for `Client` though, so I&#x27;ll pull that out into `from_env()`.</pre>

<pre>item_index: 10
created_at: 2016-09-26 21:35:24
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Move BaseTestCase to BaseIntegrationTest
body:
Intentionally -- it allows `timeout` to be passed to `from_env()`.

On Monday, 26 September 2016, Joffrey F &lt;notifications@github.com&gt; wrote:

&gt; @bfirsh &lt;https://github.com/bfirsh&gt; Looks like you accidentally included
&gt; 7f64928
&gt; &lt;https://github.com/docker/docker-py/commit/7f64928dc60b7d99d1be6ddd5e2cf6822d6127b7&gt;
&gt; ?
&gt;
&gt; —
&gt; You are receiving this because you were mentioned.
&gt; Reply to this email directly, view it on GitHub
&gt; &lt;https://github.com/docker/docker-py/pull/1217#issuecomment-249689706&gt;,
&gt; or mute the thread
&gt; &lt;https://github.com/notifications/unsubscribe-auth/AACfymN6-ZeG2XYKYLjrd9emngrWXXFIks5quCzKgaJpZM4J9xRm&gt;
&gt; .
&gt;
</pre>

<pre>item_index: 11
created_at: 2016-09-26 18:58:19
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Simplify some unnecessarily complex file structures
body:
Sure! Sounds reasonable to me - it&#x27;s plausible that it could break code and
it isn&#x27;t urgent.

On Monday, 26 September 2016, Joffrey F &lt;notifications@github.com&gt; wrote:

&gt; Not against it in principle, slightly worried about breaking stuff for
&gt; people who might have a from docker.auth.auth import or similar. May be
&gt; reasonable to put it in the 2.0 milestone?
&gt;
&gt; —
&gt; You are receiving this because you authored the thread.
&gt; Reply to this email directly, view it on GitHub
&gt; &lt;https://github.com/docker/docker-py/pull/1218#issuecomment-249662267&gt;,
&gt; or mute the thread
&gt; &lt;https://github.com/notifications/unsubscribe-auth/AACfyu1O_vx31e2z56jemOKxz4AQm028ks5quBRugaJpZM4J9373&gt;
&gt; .
&gt;
</pre>

<pre>item_index: 12
created_at: 2016-09-26 15:53:33
event_type: PullRequestEvent
repo_name: dnephin/dobi
title: Add one line install to readme
body:
None</pre>

<pre>item_index: 13
created_at: 2016-09-26 15:41:16
event_type: PullRequestEvent
repo_name: docker/example-voting-app
title: Revert &quot;Updating Worker Dockerfile&quot;
body:
Reverts docker/example-voting-app#36</pre>

<pre>item_index: 14
created_at: 2016-09-26 15:41:08
event_type: PullRequestEvent
repo_name: docker/example-voting-app
title: Revert &quot;Updating Worker Dockerfile&quot;
body:
Reverts docker/example-voting-app#36</pre>

<pre>item_index: 15
created_at: 2016-09-26 15:41:00
event_type: IssueCommentEvent
repo_name: docker/example-voting-app
title: Updating Worker Dockerfile
body:
@Hopje Thanks. Reverting until we figure out what is wrong.</pre>

<pre>item_index: 16
created_at: 2016-09-26 14:52:24
event_type: PullRequestEvent
repo_name: bfirsh/docker-api-reference
title: Add more tasks to dobi.yaml
body:
Adds the `yaml-lint`,  `swagger-json`, and `preview` tasks

You can see a few differences between dobi and make by running:
```
make validate
dobi validate
```

After the first dobi run, the `docker build` will be cached, so you don&#x27;t get the build output clutter in stdout.

`dobi preview` will run the `docker-compose` to preview the docs</pre>

<pre>item_index: 17
created_at: 2016-09-26 14:52:22
event_type: IssueCommentEvent
repo_name: bfirsh/docker-api-reference
title: Add more tasks to dobi.yaml
body:
Thanks!</pre>

<pre>item_index: 18
created_at: 2016-09-26 14:27:56
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Simplify some unnecessarily complex file structures
body:
Rebased. /cc @docker/core-docker-py-maintainers </pre>

<pre>item_index: 19
created_at: 2016-09-26 14:27:11
event_type: IssueCommentEvent
repo_name: docker/docker-py
title: Move BaseTestCase to BaseIntegrationTest
body:
Rebased. /cc @docker/core-docker-py-maintainers </pre>

<pre>item_index: 20
created_at: 2016-09-23 18:36:10
event_type: IssuesEvent
repo_name: bfirsh/docker-api-reference
title: Document container stats response
body:
None</pre>

<pre>item_index: 21
created_at: 2016-09-23 14:13:20
event_type: PullRequestEvent
repo_name: bfirsh/docker-api-reference
title: Fix 3 errors in the schema
body:
Also add dobi.yaml and a task for validating the schema.</pre>

<pre>item_index: 22
created_at: 2016-09-23 12:33:39
event_type: IssuesEvent
repo_name: bfirsh/docker-api-reference
title: Document EndpointSettings
body:
It&#x27;s not documented anywhere, even in the code.

https://github.com/docker/docker/blob/3ea762b9f6ba256cf51bd2c35988f0c48bccf0b0/api/types/network/network.go</pre>

<pre>item_index: 23
created_at: 2016-09-23 09:56:05
event_type: PullRequestEvent
repo_name: docker/example-voting-app
title: Updating Worker Dockerfile
body:
Changing base image to Microsoft&#x27;s release version</pre>

<pre>item_index: 24
created_at: 2016-09-23 09:56:04
event_type: IssueCommentEvent
repo_name: docker/example-voting-app
title: Updating Worker Dockerfile
body:
Thanks!</pre>

<pre>item_index: 25
created_at: 2016-09-21 11:26:37
event_type: IssuesEvent
repo_name: bfirsh/docker-api-reference
title: Docs say to leave &quot;auth&quot; key empty in &quot;X-Registry-Auth&quot;
body:
https://docs.docker.com/engine/reference/api/docker_remote_api/

&quot;Callers should leave the auth empty.&quot;

Is this true or can we leave this out?</pre>

<pre>item_index: 26
created_at: 2016-09-20 18:08:55
event_type: IssuesEvent
repo_name: bfirsh/docker-api-reference
title: Make source YAML and output as JSON as part of build
body:
Maybe.

Editing the JSON is a pain in the arse, particularly with blocks of markdown. The diffs in GitHub will be awful too.</pre>

<pre>item_index: 27
created_at: 2016-09-20 18:03:24
event_type: IssueCommentEvent
repo_name: bfirsh/docker-api-reference
title: Make source YAML and output as JSON as part of build
body:
Much easier to decipher: https://gist.github.com/bfirsh/2a930075a4165dd2703b886379c18498</pre>

<pre>item_index: 28
created_at: 2016-09-20 11:28:31
event_type: IssueCommentEvent
repo_name: bfirsh/django-ordered-model
title: Add top and bottom links to admin
body:
Also – any chance you could squash the fixup commits?</pre>

<pre>item_index: 29
created_at: 2016-09-20 11:26:52
event_type: IssueCommentEvent
repo_name: bfirsh/django-ordered-model
title: Add top and bottom links to admin
body:
I don&#x27;t think that branch can just be removed – it should throw an error if you use an unsupported direction.</pre>

<pre>item_index: 30
created_at: 2016-09-19 16:26:04
event_type: PullRequestReviewCommentEvent
repo_name: docker/docker-py
title: WIP: A new user-focused API
body:
No strong opinions about this, but I&#x27;m not sure I understand why using a base class is a bad thing.</pre>

<pre>item_index: 31
created_at: 2016-09-19 16:24:14
event_type: PullRequestReviewCommentEvent
repo_name: docker/docker-py
title: WIP: A new user-focused API
body:
I would much prefer to make this the primary API (`Client`) and have the low-level thing as the `SomeQualifierClient` (currently `APIClient`). Otherwise, the people using the primary API (i.e. most people) will get confused because they&#x27;re using a thing which doesn&#x27;t look like the primary API. If we&#x27;re going 2.0, we have the opportunity to break stuff like this.

The risk is that we confuse existing users who upgrade to the new API. I wonder if we can do something clever to warn them. For example, if they access an attribute which doesn&#x27;t exist, but does exist on `APIClient`, it gives them a useful error message telling them to use `client.api`.</pre>

<pre>item_index: 32
created_at: 2016-09-19 16:18:56
event_type: PullRequestReviewCommentEvent
repo_name: docker/docker-py
title: WIP: A new user-focused API
body:
Yes, good idea. I think a more general `DockerException` (or something) makes sense – it&#x27;s technically not an error from the API.</pre>

<pre>item_index: 33
created_at: 2016-09-19 14:49:24
event_type: PullRequestReviewCommentEvent
repo_name: bfirsh/django-ordered-model
title: Add top and bottom links to admin
body:
Great – thank you! :+1: </pre>

<pre>item_index: 34
created_at: 2016-09-19 14:48:52
event_type: PullRequestReviewCommentEvent
repo_name: bfirsh/django-ordered-model
title: Add top and bottom links to admin
body:
Looks like this branch isn&#x27;t needed.

Also – the `move()` method is deprecated. Perhaps `move_view` should call `top()` and `bottom()` directly?</pre>

<pre>item_index: 35
created_at: 2016-09-18 09:40:36
event_type: IssueCommentEvent
repo_name: bfirsh/jsnes
title: sound issues
body:
:+1:
</pre>

<pre>item_index: 36
created_at: 2016-09-18 09:40:36
event_type: IssuesEvent
repo_name: bfirsh/jsnes
title: sound issues
body:
In Chrome, the sound is choppy (no errors though).

In Firefox (15) when I enable sound, the game effectively pauses, dropping the framerate to 0 and giving this error with dynamicaudio-min.js:
    TypeMismatchError: The type of an object is incompatible with the expected type of the parameter associated to the object
</pre>

<pre>item_index: 37
created_at: 2016-09-18 09:40:07
event_type: IssuesEvent
repo_name: bfirsh/jsnes
title: Add Webkit Web Audio Support
body:
I see you&#x27;ve already added moz audio and a flash fallback for audio support.
There&#x27;s an api for macintosh chrome and experimental builds of safari that is similar to moz audio.
I thought you should know about http://chromium.googlecode.com/svn/trunk/samples/audio/index.html
To enable web audio support in chrome you have to enable it in about:flags</pre>

<pre>item_index: 38
created_at: 2016-09-18 09:40:05
event_type: IssueCommentEvent
repo_name: bfirsh/jsnes
title: Add Webkit Web Audio Support
body:
Wooot. Thanks @webdevbyjoss.

Now live: https://fir.sh/projects/jsnes/</pre>

<pre>item_index: 39
created_at: 2016-09-18 09:38:37
event_type: IssueCommentEvent
repo_name: bfirsh/dynamicaudio.js
title: Web Audio API support
body:
Boom. https://github.com/bfirsh/dynamicaudio.js/releases/tag/0.2</pre>

<pre>item_index: 40
created_at: 2016-09-18 09:38:37
event_type: IssuesEvent
repo_name: bfirsh/dynamicaudio.js
title: Web Audio API support
body:
`mozWriteAudio` has been phased out in favor of the much more complicated Web Audio API. It&#x27;d be nice if dynamicaudio.js tried to use Web Audio API as one of its fallbacks. The code would look something like this Gist: https://gist.github.com/bhollis/05fa5870d41d96e07aff</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      20,
      22,
      25,
      26,
      31
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      3,
      16,
      21,
      26,
      30,
      31
    ],
    &quot;description&quot;: &quot;Building and maintaining Docker API reference documentation with schema validation tooling, contributing to Docker Python client API design, and maintaining personal open-source libraries.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      2,
      4,
      5,
      6,
      8,
      9,
      10,
      11,
      18,
      19,
      30,
      31,
      32
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      16,
      26,
      31
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      8,
      16,
      21,
      26,
      30
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      16,
      21,
      26,
      27
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      16,
      21,
      26,
      30,
      31,
      32
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      26,
      27
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 04: `alekart` — `2021-07-01`

Items in bundle: 2

### Bundle text

<pre>item_index: 1
created_at: 2021-09-14 08:01:56
event_type: PullRequestEvent
repo_name: Dcode-Evo/actions-wip
title: Bump path-parse from 1.0.6 to 1.0.7
body:
Bumps [path-parse](https://github.com/jbgutierrez/path-parse) from 1.0.6 to 1.0.7.
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;See full diff in &lt;a href=&quot;https://github.com/jbgutierrez/path-parse/commits/v1.0.7&quot;&gt;compare view&lt;/a&gt;&lt;/li&gt;
&lt;/ul&gt;
&lt;/details&gt;
&lt;br /&gt;


[![Dependabot compatibility score](https://dependabot-badges.githubapp.com/badges/compatibility_score?dependency-name=path-parse&amp;package-manager=npm_and_yarn&amp;previous-version=1.0.6&amp;new-version=1.0.7)](https://docs.github.com/en/github/managing-security-vulnerabilities/about-dependabot-security-updates#about-compatibility-scores)

Dependabot will resolve any conflicts with this PR as long as you don&#x27;t alter it yourself. You can also trigger a rebase manually by commenting `@dependabot rebase`.

[//]: # (dependabot-automerge-start)
[//]: # (dependabot-automerge-end)

---

&lt;details&gt;
&lt;summary&gt;Dependabot commands and options&lt;/summary&gt;
&lt;br /&gt;

You can trigger Dependabot actions by commenting on this PR:
- `@dependabot rebase` will rebase this PR
- `@dependabot recreate` will recreate this PR, overwriting any edits that have been made to it
- `@dependabot merge` will merge this PR after your CI passes on it
- `@dependabot squash and merge` will squash and merge this PR after your CI passes on it
- `@dependabot cancel merge` will cancel a previously requested merge and block automerging
- `@dependabot reopen` will reopen this PR if it is closed
- `@dependabot close` will close this PR and stop Dependabot recreating it. You can </pre>

<pre>item_index: 2
created_at: 2021-08-10 07:37:10
event_type: PullRequestEvent
repo_name: Dcode-Evo/actions-wip
title: Bump @actions/core from 1.2.5 to 1.2.6
body:
Bumps [@actions/core](https://github.com/actions/toolkit/tree/HEAD/packages/core) from 1.2.5 to 1.2.6.
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/actions/toolkit/blob/main/packages/core/RELEASES.md&quot;&gt;@actions/core&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h3&gt;1.2.6&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/actions/toolkit/pull/571&quot;&gt;Update &lt;code&gt;exportVariable&lt;/code&gt; and &lt;code&gt;addPath&lt;/code&gt; to use environment files&lt;/a&gt;&lt;/li&gt;
&lt;/ul&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;See full diff in &lt;a href=&quot;https://github.com/actions/toolkit/commits/HEAD/packages/core&quot;&gt;compare view&lt;/a&gt;&lt;/li&gt;
&lt;/ul&gt;
&lt;/details&gt;
&lt;br /&gt;


[![Dependabot compatibility score](https://dependabot-badges.githubapp.com/badges/compatibility_score?dependency-name=@actions/core&amp;package-manager=npm_and_yarn&amp;previous-version=1.2.5&amp;new-version=1.2.6)](https://docs.github.com/en/github/managing-security-vulnerabilities/configuring-github-dependabot-security-updates)

Dependabot will resolve any conflicts with this PR as long as you don&#x27;t alter it yourself. You can also trigger a rebase manually by commenting `@dependabot rebase`.

[//]: # (dependabot-automerge-start)
[//]: # (dependabot-automerge-end)

---

&lt;details&gt;
&lt;summary&gt;Dependabot commands and options&lt;/summary&gt;
&lt;br /&gt;

You can trigger Dependabot actions by commenting on this PR:
- `@dependabot rebase` will rebase this PR
- `@dependabot recreate` will recreate this PR, overwriting</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;description&quot;: &quot;Automated dependency bump PRs in a GitHub Actions repository&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 05: `alsemyonov` — `2014-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2014-05-09 02:05:00
event_type: PullRequestEvent
repo_name: soundcloud/normailize
title: Yandex provider
body:
I have added provider for Yandex.com.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;content_community&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;Adding a Yandex.com email provider to an email normalization library&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 06: `coryodaniel` — `2018-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2018-12-31 23:15:54
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Fix dialyzer issues re: Bonny.Operator
body:
Errors around:
* EEx
* Mix</pre>

<pre>item_index: 2
created_at: 2018-12-30 20:18:13
event_type: PullRequestEvent
repo_name: h4cc/awesome-elixir
title: Add bonny (#4532)
body:
Title
Add Package &quot;bonny&quot;

Description
Resolves #4532

Commit message
Kubernetes Operator Development Framework</pre>

<pre>item_index: 3
created_at: 2018-12-30 20:11:48
event_type: IssuesEvent
repo_name: h4cc/awesome-elixir
title: Add Package &quot;bonny&quot;
body:
## Description

Add the Package &quot;bonny&quot; from hex.pm

**Link:** https://hex.pm/packages/bonny

**Description:**

Bonny: Kubernetes Operator Development Framework. Extend Kubernetes with Elixir

</pre>

<pre>item_index: 4
created_at: 2018-12-30 18:00:29
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Add --skip-deployment flag to bonny.gen.manifest
body:
For local development it would be nice to have a way to generate a manifest, without generating a deployment so the operator can be run externally to the cluster.

Add:
* [ ] mix bonny.gen.manifest --skip-deployment
* [ ] help message 

```
    To skip the `deployment` for running an operator outside of the cluster (like in development) run:
      mix bonny.gen.manifest --skip-deployment
```</pre>

<pre>item_index: 5
created_at: 2018-12-30 01:41:57
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Abstracted config module
body:
Support config free operator creation w/ sensible defaults</pre>

<pre>item_index: 6
created_at: 2018-12-29 23:51:01
event_type: IssueCommentEvent
repo_name: coryodaniel/bonny
title: Abstracted config module
body:
Closes https://github.com/coryodaniel/bonny/issues/18</pre>

<pre>item_index: 7
created_at: 2018-12-29 23:50:53
event_type: IssueCommentEvent
repo_name: coryodaniel/bonny
title: Add bonny.gen.config
body:
May not be necessary after config free setup https://github.com/coryodaniel/bonny/pull/19</pre>

<pre>item_index: 8
created_at: 2018-12-29 23:50:06
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Abstracted config module
body:
Support config free operator creation w/ sensible defaults</pre>

<pre>item_index: 9
created_at: 2018-12-29 19:04:26
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Auto detecting operator controllers for Watcher
body:
Currently you have to explicitly set the controllers to watch in config.exs. This made it easy to test. Its explicit, but it can also be error prone...

Could be detected with something like:
```elixir
controllers = 
  :code.all_loaded()
  |&gt; Enum.filter(fn({mod, _}) -&gt; 
    behaviours = mod.module_info(:attributes)[:behaviour]
    behaviours &amp;&amp; Enum.member?(behaviours, Bonny.Controller)
  end)
  |&gt; Enum.map(&amp;(elem(&amp;1,0)))
```</pre>

<pre>item_index: 10
created_at: 2018-12-29 18:47:01
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Add bonny.gen.config
body:
Create a mix task `bonny.gen.config` that will create a new configuration file @ `config/bonny.exs` with the config example and comments from the README and also inject a line in the bottom of `config/config.exs` that includes the new config file.</pre>

<pre>item_index: 11
created_at: 2018-12-29 16:57:08
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Restrict operator permissions on CRDs
body:
Operators have full access to CRDs. I think this can be lowered to *get* and *watch* only.

https://github.com/coryodaniel/bonny/blob/master/lib/bonny/operator.ex#L28</pre>

<pre>item_index: 12
created_at: 2018-12-29 16:05:39
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: WebHooks support
body:
Add support for Validating and Mutating webhooks. </pre>

<pre>item_index: 13
created_at: 2018-12-29 16:04:56
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Add a generator for an &quot;integration&quot; test suite
body:
Using the manifest generator and custom resource (#10) generator, it should be possible to deploy and verify the functionality of a CRD on a local cluster.</pre>

<pre>item_index: 14
created_at: 2018-12-29 16:03:49
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Support default labels for all resources from config.ex
body:
Add the ability to set labels for all resources created from `mix bonny.gen.manifest`

```elixir
config :bonny, labels: %{
  kewl: &quot;absolutely&quot;
}
```</pre>

<pre>item_index: 15
created_at: 2018-12-27 20:39:06
event_type: PullRequestEvent
repo_name: coryodaniel/gcbapp-dockerfile-example
title: Update helloworld.sh
body:
None</pre>

<pre>item_index: 16
created_at: 2018-12-27 20:38:48
event_type: PullRequestEvent
repo_name: coryodaniel/gcbapp-dockerfile-example
title: Update helloworld.sh
body:
None</pre>

<pre>item_index: 17
created_at: 2018-12-27 20:34:32
event_type: PullRequestEvent
repo_name: coryodaniel/gcbapp-dockerfile-example
title: Update helloworld.sh
body:
None</pre>

<pre>item_index: 18
created_at: 2018-12-22 01:41:46
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: deployment/manifest generator
body:
None</pre>

<pre>item_index: 19
created_at: 2018-12-22 01:41:41
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: deployment/manifest generator
body:
None</pre>

<pre>item_index: 20
created_at: 2018-12-21 23:48:19
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Generators and CRD/Controller naming refactor
body:
* [Added] controller generator
* [Added] readme docs
* [Added] logo
* [Added] manifest generator
* [Added] dockerfile generator</pre>

<pre>item_index: 21
created_at: 2018-12-21 23:47:08
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Generator and CRD/Controller naming refactor
body:
* [Added] controller generator
* [Added] readme docs
* [Added] logo
* [Added] manifest generator
* [Added] dockerfile generator</pre>

<pre>item_index: 22
created_at: 2018-12-21 23:18:55
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Support default labels for all resources from config.ex
body:
Add the ability to set labels for all resources created from `mix bonny.gen.manifest`

```elixir
config :bonny, labels: %{
  kewl: &quot;absolutely&quot;
}
```</pre>

<pre>item_index: 23
created_at: 2018-12-20 18:58:21
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Generator for making a custom resource&#x27;s YAML
body:
depends on https://github.com/coryodaniel/bonny/issues/9

mix bonny.gen.resource test-widget --crd widget --version v1

```yaml
apiVersion: bonny.example.io/v1
kind: Widget
metadata:
  name: test-widget
spec:
  whizbangs: 3
```</pre>

<pre>item_index: 24
created_at: 2018-12-20 18:56:08
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Open API 3 Schema Validation
body:
[Open API 3 Schema Validation](https://kubernetes.io/docs/tasks/access-kubernetes-api/custom-resources/custom-resource-definitions/#validation)

[Elixir Library](https://github.com/open-api-spex/open_api_spex)</pre>

<pre>item_index: 25
created_at: 2018-12-20 18:55:31
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Additional printed columns in kubectl
body:
https://kubernetes.io/docs/tasks/access-kubernetes-api/custom-resources/custom-resource-definitions/#additional-printer-columns</pre>

<pre>item_index: 26
created_at: 2018-12-20 18:54:54
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: API Aggregation
body:
* [ ] [API Aggregation](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/)
</pre>

<pre>item_index: 27
created_at: 2018-12-20 18:54:26
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Finalizer support
body:
https://kubernetes.io/docs/tasks/access-kubernetes-api/custom-resources/custom-resource-definitions/#finalizers</pre>

<pre>item_index: 28
created_at: 2018-12-20 18:40:28
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: dispatch handling and the Events API
body:
While it is up the the individual controller to handle error cases, it would be nice to integrate the result of a controller dispatch with the kubernetes events API.</pre>

<pre>item_index: 29
created_at: 2018-12-20 17:35:04
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Add a prometheus endpoint
body:
* [ ] Track metrics of success on dispatching
  * {apigroup, resource, version, event, success/fail}
* [ ] Add /metrics endpoint</pre>

<pre>item_index: 30
created_at: 2018-12-20 17:12:29
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Initial release
body:
    Initial release

    * [Added] Support for defining CRDs
    * [Added] GenServer to watch CRDs for events
    * [Added] Operator behavior and macro
    * [Added] RBAC rule generation</pre>

<pre>item_index: 31
created_at: 2018-12-20 17:11:40
event_type: PullRequestEvent
repo_name: coryodaniel/bonny
title: Initial release
body:
    Initial release

    * [Added] Support for defining CRDs
    * [Added] GenServer to watch CRDs for events
    * [Added] Operator behavior and macro
    * [Added] RBAC rule generation</pre>

<pre>item_index: 32
created_at: 2018-12-20 02:58:03
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Dispatch operator events in a task
body:
Consider dispatch operator events in a task. We expect the operator to handle its own errors, so dispatch in a task could make it extra speedy.

```elixir
defmodule Bonny.TestTaskSupervisor do
  def async_nolink(_, fun), do: fun.()
  def start_child(_, fun), do: fun.()
end

@task_supervisor Application.get_env(:bonny, :task_supervisor) || Task.Supervisor
```</pre>

<pre>item_index: 33
created_at: 2018-12-20 02:16:28
event_type: IssuesEvent
repo_name: coryodaniel/bonny
title: Fix dialyzer issues re: Bonny.Operator
body:
**When not using attributes results in**
```
[ElixirLS Dialyzer] Invalid type specification for function &#x27;Elixir.V1.Whizbang&#x27;:crd_spec/0. The success typing is () -&gt; #{&#x27;__struct__&#x27;:=&#x27;Elixir.Bonny.CRD&#x27;, &#x27;group&#x27;:=&#x27;nil&#x27; | &lt;&lt;_:128&gt;&gt;, &#x27;names&#x27;:=&#x27;nil&#x27; | #{&#x27;kind&#x27;:=atom() | binary(), &#x27;plural&#x27;:=&lt;&lt;_:8,_:_*8&gt;&gt;, &#x27;short_names&#x27;:=&#x27;nil&#x27;, &#x27;singular&#x27;:=binary()}, &#x27;scope&#x27;:=&#x27;namespaced&#x27; | &#x27;nil&#x27;, &#x27;version&#x27;:=&#x27;nil&#x27; | binary()}
```

**When using attributes results in these warnings:**
```
[Elixir] this check/guard will always yield the same result
[ElixirLS Dialyzer] Invalid type specification for function &#x27;Elixir.V2.Whizbang&#x27;:crd_spec/0. The success typing is () -&gt; #{&#x27;__struct__&#x27;:=&#x27;Elixir.Bonny.CRD&#x27;, &#x27;group&#x27;:=&lt;&lt;_:120&gt;&gt;, &#x27;names&#x27;:=#{&#x27;kind&#x27;:=&lt;&lt;_:24&gt;&gt;, &#x27;plural&#x27;:=&lt;&lt;_:32&gt;&gt;, &#x27;singular&#x27;:=&lt;&lt;_:24&gt;&gt;}, &#x27;scope&#x27;:=&#x27;cluster&#x27;, &#x27;version&#x27;:=&lt;&lt;_:64&gt;&gt;}
[ElixirLS Dialyzer] Function crd_spec_names/1 will never be called
[ElixirLS Dialyzer] Guard test __@10::#{&#x27;kind&#x27;:=&lt;&lt;_:24&gt;&gt;, &#x27;plural&#x27;:=&lt;&lt;_:32&gt;&gt;, &#x27;singular&#x27;:=&lt;&lt;_:24&gt;&gt;} =:= &#x27;false&#x27; can never succeed
```</pre>

<pre>item_index: 34
created_at: 2018-12-19 21:06:16
event_type: IssuesEvent
repo_name: coryodaniel/k8s_conf
title: Add support for `auth-provider`
body:
Add support for [`auth-provider` auth](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#option-1-oidc-authenticator)</pre>

<pre>item_index: 35
created_at: 2018-12-19 21:05:43
event_type: IssuesEvent
repo_name: coryodaniel/k8s_conf
title: Support kube `exec` auth
body:
Add support for [`exec` auth](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#configuration)
</pre>

<pre>item_index: 36
created_at: 2018-12-19 21:05:07
event_type: IssuesEvent
repo_name: coryodaniel/k8s_conf
title: Fix `mix dialyzer` output
body:
A few of the type specs are amiss.</pre>

<pre>item_index: 37
created_at: 2018-12-14 19:55:55
event_type: PullRequestEvent
repo_name: terraform-google-modules/terraform-google-kubernetes-engine
title: Support for disabling basic auth / client cert
body:
* [Added] `enable_basic_auth` variable. defaults to `false`&lt;sup&gt;1&lt;/sup&gt;
* [Added] `basic_auth_username` variable. defaults to `&quot;&quot;`
* [Added] `basic_auth_password` variable. defaults to `&quot;&quot;`
* [Added] `issue_client_certificate` variable. defaults to
`true`&lt;sup&gt;2&lt;/sup&gt;

Notes:

1. This will cause a plan change for existing users. Enabling it will
require them to set a username and password.

2. This is enabled by default, despite being a poor security practice
because changing this value is destructive to the cluster and we decided
to err on not trigger *destroy* plan changes to existing users.</pre>

<pre>item_index: 38
created_at: 2018-12-14 18:21:39
event_type: IssueCommentEvent
repo_name: terraform-google-modules/terraform-google-kubernetes-engine
title: Support for disabling basic auth &amp; client certificate
body:
Yep, I got that support in my first pass! Thanks for the input, sounds like a good approach to me.</pre>

<pre>item_index: 39
created_at: 2018-12-13 17:19:39
event_type: IssuesEvent
repo_name: terraform-google-modules/terraform-google-network
title: Renaming a secondary range returns CIDR conflict with self
body:
Renaming a secondary ip range returns an error that the CIDR address range is conflicting.

```
module.test-vpc-module.google_compute_subnetwork.subnetwork[0]: Modifying... (ID: us-west1/subnet-01)
  secondary_ip_range.0.range_name: &quot;subnet-01-secondary-01&quot; =&gt; &quot;subnet-01-secondary-pods&quot;

Error: Error applying plan:

1 error(s) occurred:

* module.test-vpc-module.google_compute_subnetwork.subnetwork[0]: 1 error(s) occurred:

* google_compute_subnetwork.subnetwork.0: Error updating Subnetwork &quot;us-west1/subnet-01&quot;: googleapi: Error 400: Invalid value for field &#x27;resource.secondaryIpRanges[0].ipCidrRange&#x27;: &#x27;192.168.64.0/24&#x27;. Invalid IPCidrRange: 192.168.64.0/24 conflicts with existing subnetwork &#x27;subnet-01&#x27; in region &#x27;us-west1&#x27;., invalid
```</pre>

<pre>item_index: 40
created_at: 2018-12-13 01:54:46
event_type: IssuesEvent
repo_name: terraform-google-modules/terraform-google-kubernetes-engine
title: Update examples to include example of setting service account
body:
I was setting up a cluster with this module using the examples as a reference and kept running into issues about the service account not existing (I set up the project with the project factory).

As noted in the [README](https://github.com/terraform-google-modules/terraform-google-kubernetes-engine/blame/master/README.md#L42)&lt;sup&gt;1&lt;/sup&gt; the node pools should specify the service account. I got tripped up on this since it wasn&#x27;t in the examples. 

It could be helpful to add a note in the examples or in the examples&#x27; README.

Looks like issue #23 would also resolve this.

*Footnotes:*

1. pardon the blame view, needed to link to the line in the readme</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      5,
      20,
      30
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      2,
      3,
      5,
      20,
      30,
      31
    ],
    &quot;description&quot;: &quot;Bonny, an Elixir framework for building Kubernetes Operators, with CRD support, controller and manifest generators, and config-free operator creation. Also k8s_conf for Kubernetes config parsing.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      30,
      31,
      37,
      38,
      2,
      3
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      30,
      31
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      30,
      31,
      5,
      20,
      34,
      35,
      37
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      20,
      30,
      31,
      5
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      20,
      30,
      31,
      5,
      37,
      38
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      30,
      31
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;implicit&quot;
  }
}</pre>

## Bundle 07: `aliscott` — `2017-01-01`

Items in bundle: 14

### Bundle text

<pre>item_index: 1
created_at: 2017-03-29 14:43:34
event_type: IssueCommentEvent
repo_name: openshift/origin
title: Multiple EgressNetworkPolicies in same net namespace with ovs-multitenant SDN
body:
@danwinship It&#x27;s happening randomly. The issue goes away when I restart origin-node.</pre>

<pre>item_index: 2
created_at: 2017-03-29 10:01:32
event_type: IssueCommentEvent
repo_name: openshift/origin
title: Multiple EgressNetworkPolicies in same net namespace with ovs-multitenant SDN
body:
@danwinship I have started seeing this issue again in OpenShift 1.4.1

The difference this time is it is detecting the same single EgressNetworkPolicy multiple times:
```
multiple EgressNetworkPolicies in same network namespace (ali-test-1:default, ali-test-1:default) is not allowed; dropping all traffic
```

**Version**
```
[root@master3 ~]# oc version
oc v1.4.1
kubernetes v1.4.0+776c994
features: Basic-Auth GSSAPI Kerberos SPNEGO

Server https://dashboard.abarcloud.internal:8443
openshift v1.4.1
kubernetes v1.4.0+776c994
```</pre>

<pre>item_index: 3
created_at: 2017-03-27 12:30:30
event_type: PullRequestReviewCommentEvent
repo_name: kubernetes/kubernetes
title: Fix original error being overwritten before returned
body:
Thanks, fixed</pre>

<pre>item_index: 4
created_at: 2017-03-06 11:46:20
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Readiness probe failed: Job glusterd.service/start failed with result &#x27;dependency&#x27; when deploying on kubernetes
body:
@humblec here are the glusterd logs:

[etc-glusterfs-glusterd.vol.log.txt](https://github.com/heketi/heketi/files/820979/etc-glusterfs-glusterd.vol.log.txt)

And below is the events of the gluster pod when I run a redeploy.

Note: If I make sure the existing pod is terminated before I deploy the new pod then everything works as expected (e.g. scale to 0, wait for the old pod to terminate then redeploy and scale back to 1). This only happens when the old pod is still terminating when the new pod starts.


```
Events:
  FirstSeen	LastSeen	Count	From									SubobjectPath			Type		Reason		Message
  ---------	--------	-----	----									-------------			--------	------		-------
  6m		6m		1	{default-scheduler }											Normal		Scheduled	Successfully assigned glusterfs-dc-node-aa3991db123d-6-wz58c to node-aa3991db123d
  6m		6m		1	{kubelet node-aa3991db123d}	spec.containers{glusterfs}	Normal		Created		Created container with docker id 80ddd348abbd; Security:[seccomp=unconfined]
  6m		6m		1	{kubelet node-aa3991db123d}	spec.containers{glusterfs}	Normal		Started		Started container with docker id 80ddd348abbd
  4m		4m		3	{kubelet node-aa3991db123d}	spec.containers{glusterfs}	Warning		Unhealthy	Liveness probe failed: ● glusterd.service - GlusterFS, a clustered file-system server
   Loaded: loaded (/usr/lib/systemd/system/glusterd.service; enabled; vendor preset: disabled)
   Active: inactive (dead)

Mar 06 11:34:18 node-aa3991db123d systemd[1]: Dependency failed for </pre>

<pre>item_index: 5
created_at: 2017-03-06 10:45:01
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Readiness probe failed: Job glusterd.service/start failed with result &#x27;dependency&#x27; when deploying on kubernetes
body:
@humblec I currently have it deployed with `rpcbind.service` and `rpcbind.socket` stopped and disabled on the hosts and am still seeing this issue.</pre>

<pre>item_index: 6
created_at: 2017-03-04 12:53:00
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Openshift Origin: scaling heketi for multiple replicas not working
body:
@lpabon thanks! Will the new secret implementation for the database work with OpenShift? I see it is already in the deployment yaml for Kubernetes, but not OpenShift yet.</pre>

<pre>item_index: 7
created_at: 2017-02-26 18:27:14
event_type: IssueCommentEvent
repo_name: openshift/origin
title: Is it possible to scope LimitRanges?
body:
:+1: What I really want to do is let my build pods be burstable and my other pods to have guaranteed resources, so this may work for me. Is there any way to do this currently?</pre>

<pre>item_index: 8
created_at: 2017-02-26 10:53:22
event_type: IssueCommentEvent
repo_name: openshift/origin
title: Glusterfs with network encryption fails mounting when single node is down
body:
I&#x27;m also having this problem when only management encryption is enabled.</pre>

<pre>item_index: 9
created_at: 2017-02-22 14:53:47
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Openshift Origin: scaling heketi for multiple replicas not working
body:
This also causes an issue when the single heketi pod is recreated.

Since the old pod is still terminating when the new one is created, the new pod opens the db in read-only mode, with this warning:
```
Unable to open database.  Retrying using read only mode
```

To get round this I&#x27;ve added `terminationGracePeriodSeconds: 0` to the heketi deployment config.</pre>

<pre>item_index: 10
created_at: 2017-02-21 09:42:34
event_type: IssuesEvent
repo_name: heketi/heketi
title: Openshift Origin: scaling heketi for multiple replicas not working
body:
Using OpenShift Origin 1.4.1 and heketi-cli v4.0.0, I&#x27;m trying to scale up the heketi deployment config so it is highly available.

After following https://github.com/heketi/heketi/wiki/OpenShift-Integration---Project-Aplo I run:
```
oc scale --replicas=2 dc/heketi
```

The new heketi pod will fail to get to the `Ready` state with the following errors:
```
  5m		17s		7	{kubelet master1}	spec.containers{heketi}	Warning		Unhealthy	Liveness probe failed: Get http://10.128.0.70:8080/hello: dial tcp 10.128.0.70:8080: getsockopt: connection refused
  5m		7s		36	{kubelet master1}	spec.containers{heketi}	Warning		Unhealthy	Readiness probe failed: Get http://10.128.0.70:8080/hello: dial tcp 10.128.0.70:8080: getsockopt: connection refused
```</pre>

<pre>item_index: 11
created_at: 2017-02-18 07:11:12
event_type: PullRequestEvent
repo_name: kubernetes/kubernetes
title: Fix original error being overwritten before returned
body:
None</pre>

<pre>item_index: 12
created_at: 2017-02-16 09:20:37
event_type: IssuesEvent
repo_name: openshift/origin
title: Glusterfs with network encryption fails mounting when single node is down
body:
Glusterfs volume fails to mount when client/server network encryption is enabled and a single gluster node is unavailable

##### Version
```
openshift v1.4.1
kubernetes v1.4.0+776c994
etcd 3.1.0-rc.0
```

##### Steps To Reproduce
1. Create a persistent-volume-claim that uses glusterfs dynamic provisioning.
2. Stop the volume, enable client.ssl and server.ssl and restart the volume.
3. Mount the volume to a pod.
4. Test reading and writing files to the volume. Everything works fine at this stage.
5. Shut down a single glusterfs node
4. Test reading and writing files to the volume.

##### Expected Result

I should be able to mount the volume and it should still be readable and writeable, since 2/3 of the gluster nodes are still running.

##### Current Result
Neither reading or writing to the volume works. When recreating the pod the volume fails to mount:
```
8s  8s  1 {kubelet node-fbcb9413635c}   Warning  FailedMount Unable to mount volumes for pod &quot;nginx_test1(867619c0-dcc3-11e6-9ab1-06ff73935133)&quot;: timeout expired waiting for volumes to attach/mount for pod &quot;nginx&quot;/&quot;test1&quot;. list of unattached/unmounted volumes=[mypd]
8s  8s  1 {kubelet node-fbcb9413635c}   Warning  FailedSync Error syncing pod, skipping: timeout expired waiting for volumes to attach/mount for pod &quot;nginx&quot;/&quot;test1&quot;. list of unattached/unmounted volumes=[mypd]
```

The volume works again when I bring up unavailable node or if I disable client and server SSL.

##### Additional Infor</pre>

<pre>item_index: 13
created_at: 2017-01-23 11:48:54
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Readiness probe failed: Job glusterd.service/start failed with result &#x27;dependency&#x27; when deploying on kubernetes
body:
@MohamedAshiqrh I&#x27;m running:
CentOS Linux release 7.3.1611 (Core) with rpcbind-0.2.0-38.el7.src.rpm</pre>

<pre>item_index: 14
created_at: 2017-01-20 09:19:01
event_type: IssueCommentEvent
repo_name: heketi/heketi
title: Readiness probe failed: Job glusterd.service/start failed with result &#x27;dependency&#x27; when deploying on kubernetes
body:
I&#x27;m seeing this issue when redeploying the glusterfs pods. `glusterd` won&#x27;t start on the new pod until the old pod has fully terminated so it always fails the first readiness probe. Disabling `rpcbind.socket` and `rpcbind.service` on the host node doesn&#x27;t have any effect.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      10,
      12,
      4,
      14
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;infrastructure&quot;,
    &quot;citations&quot;: [
      10,
      12,
      1,
      2,
      8,
      14
    ],
    &quot;description&quot;: &quot;Operating and troubleshooting OpenShift/Kubernetes clusters with Heketi-managed GlusterFS storage, including HA scaling, network encryption, and SDN egress policy issues.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      5,
      6,
      13,
      14
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      10,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      10,
      12,
      1,
      4,
      8
    ],
    &quot;value&quot;: 3
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      10,
      9,
      8,
      12
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      10,
      12,
      4,
      14,
      9
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 08: `cunzi` — `2016-07-01`

Items in bundle: 4

### Bundle text

<pre>item_index: 1
created_at: 2016-08-19 09:36:32
event_type: PullRequestEvent
repo_name: cunzi/mapping.cunzi.xyz
title: Revert &quot;Revert &quot;解决map中保存的数据类型和bean数据类型不匹配的问题&quot;&quot;
body:
None</pre>

<pre>item_index: 2
created_at: 2016-08-19 09:33:28
event_type: PullRequestEvent
repo_name: cunzi/mapping.cunzi.xyz
title: Revert &quot;Revert &quot;解决map中保存的数据类型和bean数据类型不匹配的问题&quot;&quot;
body:
This reverts commit 90e739864f48eb0d1ea450803aad1ea869721b4e.</pre>

<pre>item_index: 3
created_at: 2016-08-19 07:20:38
event_type: PullRequestEvent
repo_name: cunzi/mapping.cunzi.xyz
title: Feature
body:
None</pre>

<pre>item_index: 4
created_at: 2016-08-19 07:11:09
event_type: PullRequestEvent
repo_name: cunzi/mapping.cunzi.xyz
title: Feature
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;description&quot;: &quot;Personal mapping web application (mapping.cunzi.xyz) with bug fixes around data type handling between map storage and bean objects&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 09: `bcaffo` — `2018-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2018-06-26 19:14:50
event_type: PullRequestEvent
repo_name: bcaffo/MriCloudR
title: Package Actually works
body:
Toyed around with some of the functions to get them to work finally.  See the README for an example.  I&#x27;m not sure the results look good though</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;The user is working on an R package (MriCloudR) that interfaces with MRI cloud services, getting functions to work and providing README examples.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 10: `alokomkar` — `2019-07-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2019-07-18 06:13:10
event_type: IssuesEvent
repo_name: viztushar/syntax_highlighter
title: Syntax highlighter doesn&#x27;t expand beyond 5 lines - Web
body:
I am trying to come up with a code editor which takes input from a text form field and shows the output on a Rich Text widget using DartSyntaxHighlighter.

While it works fine for a short snippet of code, it doesn&#x27;t show all the code for a larger snippet. Here&#x27;s what I&#x27;ve done so far :

```
class CodeEditorWidget extends StatefulWidget {

  CodeEditorWidget();

  @override
  _ContentWidgetState createState() {
    return _ContentWidgetState();
  }
}

class _ContentWidgetState extends BaseState&lt;CodeEditorWidget&gt; {

  String _currentCode = &quot;&quot;;

  @override
  void initializeData() {
    _currentCode = &quot;class HelloWorld {\n&quot;
        &quot;public static void main() {\n&quot;
        &quot;System.out.println(\&quot;Hello again\&quot;);\n&quot;
        &quot;}\n&quot;
        &quot;}&quot;;
    _contentController.addListener(() {
      _currentCode = _contentController.value.text;
      setState(() {

      });
    });
  }

  @override
  Widget build(BuildContext context) =&gt; _buildContent();

  Widget _buildContent() {
    //return _buildBody();
    userState = AppStateWidget.of(context).userState;
    return _buildBody();
  }

  Scaffold _buildBody() =&gt; Scaffold(
    key: _scaffoldLoginKey,
    appBar: buildAppBar(&quot;Code Editor&quot;),
    body: _buildCodeEditor(),
    floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
    floatingActionButton: _buildFab(),
  );

  _buildCodeEditor() =&gt; Card(
    margin: const EdgeInsets.fromLTRB(BaseState.horizontalMargin, 0, BaseSta</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;Flutter/Dart code editor widget using DartSyntaxHighlighter&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 3
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;implicit&quot;
  }
}</pre>

## Bundle 11: `bergpb` — `2017-10-01`

Items in bundle: 8

### Bundle text

<pre>item_index: 1
created_at: 2017-12-12 14:29:18
event_type: IssueCommentEvent
repo_name: rodrigorf/filmes-cartaz-json
title: passando page pela url
body:
:+1::+1:</pre>

<pre>item_index: 2
created_at: 2017-12-12 13:51:27
event_type: IssueCommentEvent
repo_name: rodrigorf/filmes-cartaz-json
title: passando page pela url
body:
e sim rodrigo a mesma ja esta dando suporte a esta versão, subi o código para o heroku e esta funcional.</pre>

<pre>item_index: 3
created_at: 2017-12-12 13:44:29
event_type: IssueCommentEvent
repo_name: rodrigorf/filmes-cartaz-json
title: passando page pela url
body:
desculpe a demora, não tinha reparado que a mesma já retornava automaticamente.
Tinha feito isso apenas para quando o usuário tentar percorrer uma página maior que a permitida pelo site ele retorna a os últimos filmes lançados na api.</pre>

<pre>item_index: 4
created_at: 2017-12-02 19:56:16
event_type: PullRequestEvent
repo_name: rodrigorf/filmes-cartaz-json
title: passando page pela url
body:
agora pode ver os filmes lancados anteriormente percorrendo as paginas permitidas pelo site.</pre>

<pre>item_index: 5
created_at: 2017-11-16 15:18:01
event_type: PullRequestEvent
repo_name: bergpb/3it_selecao
title: Create JP
body:
vraau</pre>

<pre>item_index: 6
created_at: 2017-11-06 00:54:59
event_type: IssuesEvent
repo_name: rodrigorf/filmes-cartaz-json
title: Api Retorna Json Vazio
body:
Realizei o clone da aplicação na minha máquina e ao consultar a rota da api a mesma retornou um valor vazio:

{
  &quot;filmes&quot;: [
    
  ]
}

Provavelmente o html da página em questão foi modificado, estarei olhando essa semana se consigo corrigir e envio um pull-request para o projeto.
E parabéns pelo tutorial ótimo para quem está começando com o flask.</pre>

<pre>item_index: 7
created_at: 2017-11-04 03:36:23
event_type: IssuesEvent
repo_name: wilsonfreitas/python-bizdays
title: Fail to get bizday
body:
My code:

from bizdays import Calendar
holidays = [&#x27;2017-01-01&#x27;,&#x27;2017-04-2017&#x27;,&#x27;2017-05-2017&#x27;,&#x27;2017-09-07&#x27;,&#x27;2017-10-12&#x27;,&#x27;2017-11-11&#x27;,&#x27;2017-11-15&#x27;,&#x27;2017-12-25&#x27;]
cal = Calendar(holidays=holidays, weekdays=[&#x27;Sunday&#x27;, &#x27;Saturday&#x27;])
cal.isbizday(&#x27;2017-11-01&#x27;)

The output:
Traceback (most recent call last):
  File &quot;dias_uteis.py&quot;, line 10, in &lt;module&gt;
    cal = Calendar(holidays=holidays, weekdays=[&#x27;Sunday&#x27;, &#x27;Saturday&#x27;])
  File &quot;/usr/local/lib/python2.7/dist-packages/bizdays.py&quot;, line 285, in __init__
    self._holidays = [Date(d) for d in holidays]
  File &quot;/usr/local/lib/python2.7/dist-packages/bizdays.py&quot;, line 245, in __init__
    d = datetime.strptime(d, format).date()
  File &quot;/usr/lib/python2.7/_strptime.py&quot;, line 328, in _strptime
    data_string[found.end():])
ValueError: unconverted data remains: 17
*Test on cloud9 ide.

</pre>

<pre>item_index: 8
created_at: 2017-11-01 11:43:35
event_type: IssuesEvent
repo_name: aTItudeDeVeloper/DuCompras-trabalho-de-PIA
title: Fail to save in database
body:
**I try to save one item, and one list but not save in database.**
</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      3,
      6,
      7
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      4,
      6
    ],
    &quot;description&quot;: &quot;Contributing bug fixes and pagination features to a Flask-based movie listings JSON API, and reporting issues in Python libraries&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      6
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      6,
      7
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      4,
      6,
      7,
      8
    ],
    &quot;value&quot;: 2
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2,
      4
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      3,
      6,
      7
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 12: `crlcu` — `2015-01-01`

Items in bundle: 9

### Bundle text

<pre>item_index: 1
created_at: 2015-03-25 19:46:58
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: possible fixes
body:
[v2.0.0](https://github.com/crlcu/multiselect/tree/v2.0.0) has now a [demo page](http://crlcu.github.io/multiselect/) with [Bootstrap 3](http://getbootstrap.com/)</pre>

<pre>item_index: 2
created_at: 2015-03-25 19:46:58
event_type: IssuesEvent
repo_name: crlcu/multiselect
title: possible fixes
body:
Thank you for your multiselect code!

Still testing this but these are a few things that caught my eye:
1. upgrade to newer boostrap
2. I&#x27;m not a jquery guy but the focus stays on the middle buttons when clicked
3. possibly a way to automate the size=&#x27;8&#x27; attribute

This is what I&#x27;m using for html

```
&lt;div class=&quot;row&quot;&gt;
	&lt;div class=&quot;col-sm-5&quot;&gt;
		&lt;select name=&quot;from&quot; id=&quot;multiselect&quot; class=&quot;col-sm-12&quot; size=&quot;12&quot; multiple=&quot;multiple&quot;&gt;
			&lt;option value=&quot;1&quot;&gt;Item 1&lt;/option&gt;
			&lt;option value=&quot;2&quot;&gt;Item 5&lt;/option&gt;
			&lt;option value=&quot;2&quot;&gt;Item 2&lt;/option&gt;
			&lt;option value=&quot;2&quot;&gt;Item 4&lt;/option&gt;
			&lt;option value=&quot;3&quot;&gt;Item 3&lt;/option&gt;
		&lt;/select&gt;
	&lt;/div&gt;

	&lt;div class=&quot;col-sm-2&quot;&gt;
		&lt;button type=&quot;button&quot; id=&quot;multiselect_rightAll&quot; class=&quot;btn btn-default btn-block&quot;&gt;&lt;i class=&quot;fa fa-fast-forward fa-fw&quot;&gt;&lt;/i&gt;&lt;/button&gt;
		&lt;button type=&quot;button&quot; id=&quot;multiselect_rightSelected&quot; class=&quot;btn btn-default btn-block&quot;&gt;&lt;i class=&quot;fa fa-chevron-right fa-fw&quot;&gt;&lt;/i&gt;&lt;/button&gt;
		&lt;button type=&quot;button&quot; id=&quot;multiselect_leftSelected&quot; class=&quot;btn btn-default btn-block&quot;&gt;&lt;i class=&quot;fa fa-chevron-left fa-fw&quot;&gt;&lt;/i&gt;&lt;/button&gt;
		&lt;button type=&quot;button&quot; id=&quot;multiselect_leftAll&quot; class=&quot;btn btn-default btn-block&quot;&gt;&lt;i class=&quot;fa fa-fast-backward fa-fw&quot;&gt;&lt;/i&gt;&lt;/button&gt;
	&lt;/div&gt;

	&lt;div class=&quot;col-sm-5&quot;&gt;
		&lt;select name=&quot;to&quot; id=&quot;multiselect_to&quot; class=&quot;col-sm-12&quot; size=&quot;12&quot; multiple=&quot;multiple&quot;&gt;&lt;/select&gt;
	&lt;/div&gt;
&lt;/div&gt;
```


</pre>

<pre>item_index: 3
created_at: 2015-03-25 19:45:28
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: Undo and redo
body:
[v2.0.0](https://github.com/crlcu/multiselect/tree/v2.0.0) now supports undo and redo</pre>

<pre>item_index: 4
created_at: 2015-03-25 19:45:28
event_type: IssuesEvent
repo_name: crlcu/multiselect
title: Undo and redo
body:
I would like to have undo and redo for this. If I have time I might look into it but for now this is just a feature request :)

I think this could be implemented by giving each option an id and creating a list of command-objects that contain a set of ids and a direction. When undo is called it simply looks at the direction and does the opposite with all options that are listed. Then the command-object is moved to a redo list. Every time the user clicks an action the redo list is emptied.</pre>

<pre>item_index: 5
created_at: 2015-03-25 10:05:13
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: Undo and redo
body:
Hi @elm 

I&#x27;ve created a branch &quot;undo_redo&quot; and I implemented the undo / redo functionality.
I really appreciate if you can have a look and test it.</pre>

<pre>item_index: 6
created_at: 2015-03-24 17:48:09
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: double-click not working in new IE (11 and 12)
body:
Hi @chaau 
The bug should be fixed now.

Thanks for letting me know about this issue.</pre>

<pre>item_index: 7
created_at: 2015-03-24 17:48:09
event_type: IssuesEvent
repo_name: crlcu/multiselect
title: double-click not working in new IE (11 and 12)
body:
There is a hack in the code to support the double-click:

```javascript
				// dblclick support for IE
				if ( navigator.userAgent.match(/MSIE/i) ) {
					self.left.dblclick(function(e){
						actions.rightSelected.trigger(&#x27;click&#x27;);
					});
					
					self.right.dblclick(function(e){
						actions.leftSelected.trigger(&#x27;click&#x27;);
					});
				}
```
The useragent string got changed in the newer versions of IE. The code needs to be enhanced. Check this out: http://stackoverflow.com/questions/19999388/jquery-check-if-user-is-using-ie

The proposed enhancement is:

```javascript
				// dblclick support for IE
				if ( navigator.userAgent.match(/MSIE/i)  || navigator.userAgent.indexOf(&#x27;Trident/&#x27;) &gt; 0 || navigator.userAgent.indexOf(&#x27;Edge/&#x27;) &gt; 0) {
```
</pre>

<pre>item_index: 8
created_at: 2015-02-19 10:40:16
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: possible fixes
body:
Hi @illuminate3 

1. I would really appreciate if you can do a &quot;bootstrap3.html&quot; version which will use the latest bootstrap and create a pull request.
2. I made a change to remove focus from clicked button.
3. Regarding size=&quot;8&quot;, I&#x27;m not sure if it needs changing, because it&#x27;s up to the dev that is using this plugin to choose which will be the size for his &quot;select&quot; elements.</pre>

<pre>item_index: 9
created_at: 2015-01-11 08:37:15
event_type: IssueCommentEvent
repo_name: crlcu/multiselect
title: Undo and redo
body:
Hi @elm,

I would be nice if you can have a look and implement this feature.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;description&quot;: &quot;Maintaining and enhancing a jQuery multiselect UI plugin (crlcu/multiselect), including undo/redo functionality, IE double-click bug fixes, and a Bootstrap 3 demo page&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      5,
      6,
      8,
      9
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      8
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 13: `dariuszseweryn` — `2013-04-01`

Items in bundle: 6

### Bundle text

<pre>item_index: 1
created_at: 2013-06-03 10:03:00
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: Refactoring
body:
None</pre>

<pre>item_index: 2
created_at: 2013-05-24 08:46:38
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: Io error handling
body:
Neciu - please add error handling to convert.py</pre>

<pre>item_index: 3
created_at: 2013-05-23 09:30:53
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: Little fix in strings.
body:
None</pre>

<pre>item_index: 4
created_at: 2013-05-20 12:21:56
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: A more pythonic way of code writing.
body:
None</pre>

<pre>item_index: 5
created_at: 2013-05-16 09:55:54
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: Unused class sweeping
body:
None</pre>

<pre>item_index: 6
created_at: 2013-05-16 08:27:08
event_type: PullRequestEvent
repo_name: Polidea/ResourceSweeper
title: Unused class sweeping
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6
    ],
    &quot;description&quot;: &quot;Contributing to ResourceSweeper, a Python tool for sweeping unused resources/classes in Android projects&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: &quot;team_forming&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      4
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 14: `clrjunkie` — `2017-01-01`

Items in bundle: 2

### Bundle text

<pre>item_index: 1
created_at: 2017-03-24 20:26:17
event_type: IssueCommentEvent
repo_name: dotnet/coreclr
title: coreclr education
body:
Great Job! @mattwarren 

Now consider scaling this out by converting the content into Markdown format and submitting it as a pull request for this issue!

That way it would be super easy for CoreCLR team members to review/update/improve the content and will allow the community a simple way to provide feedback, open documentation issues concerning this area and also submit code snippets that illustrate key processing stages.
</pre>

<pre>item_index: 2
created_at: 2017-03-18 15:11:24
event_type: IssueCommentEvent
repo_name: dotnet/corefx
title: Allow to configure IO awaited Tasks to complete on the IOCP worker thread.
body:
@davidfowl Yes. and as stated at the beginning of this issue it&#x27;s tedious and code bloat with SynchronizationContext most of the time the next operation is also an enqueue to IOCP (e.g Database socket call) so there is no need to switch to another thread for that.. quite frankly I don&#x27;t see any obvious use-case that would justify a thread switch .. Windows thread pool will release another thread if an IO thread blocks and if I recall correctly it maintains 1000 of those just waiting to kick-in...

@kouvel This issue is open more than year... What exact information is missing?
</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;description&quot;: &quot;Contributing technical feedback and suggestions to .NET runtime (CoreCLR, CoreFX) issues, including documentation workflow improvements and IO thread scheduling discussions.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 15: `bit111` — `2017-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2017-05-12 09:49:37
event_type: PullRequestEvent
repo_name: spender-sandbox/cuckoo-modified
title: improved WSF file type recognition
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;security&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;Contributing a pull request to improve file-type recognition in the cuckoo-modified malware sandbox project&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 16: `crohr` — `2019-01-01`

Items in bundle: 38

### Bundle text

<pre>item_index: 1
created_at: 2019-03-20 14:11:47
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Manually copy table from boards to forums to avoid index errors
body:
```suggestion
    # Create the new table, then copy from the old table to ensure indexes are correct
```</pre>

<pre>item_index: 2
created_at: 2019-03-20 09:05:12
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Allow to override settings when executing the worker in --seed mode
body:
Tested on PullPreview and it appears to work (http://9085c9921a0a328aa8d49fc7c4d6072a77177460.my.pullpreview.com/settings)</pre>

<pre>item_index: 3
created_at: 2019-03-20 08:54:53
event_type: PullRequestEvent
repo_name: opf/openproject
title: Allow to override settings when executing the worker in --seed mode
body:
Also removing config/database.docker.yml, which seems to be no longer used.</pre>

<pre>item_index: 4
created_at: 2019-03-15 09:35:17
event_type: PullRequestEvent
repo_name: opf/openproject
title: Update docker install
body:
None</pre>

<pre>item_index: 5
created_at: 2019-03-14 16:54:07
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
It appears that the new image is 220MB less than before (638 vs 855). Well done!</pre>

<pre>item_index: 6
created_at: 2019-03-14 16:52:32
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
Tested against an existing community:8 install and the upgrade works fine, even with existing volumes attached.</pre>

<pre>item_index: 7
created_at: 2019-03-14 16:02:27
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
Also: https://hub.docker.com/r/openproject/community is out of date</pre>

<pre>item_index: 8
created_at: 2019-03-14 15:43:05
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
Note that this also modifies the paths at which the postgres data and openproject files were stored. We might to add some symlinks to offer a smooth transition for existing installs.</pre>

<pre>item_index: 9
created_at: 2019-03-14 15:40:25
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
Updated to allow for running discrete commands (e.g. `docker run IMAGE ./docker/web`) while still defaulting to the all-in-one command.

Also suppressed some output, and redirected all output from programs launched by supervisord to stderr and stdout.</pre>

<pre>item_index: 10
created_at: 2019-03-14 08:28:39
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
```suggestion
      echo &quot;-----&gt; Ensure $APP_PATH is owned by $APP_USER&quot;
```</pre>

<pre>item_index: 11
created_at: 2019-03-14 08:28:10
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
```suggestion
		chown $APP_USER.$APP_USER &quot;$PLUGIN_GEMFILE&quot;
```</pre>

<pre>item_index: 12
created_at: 2019-03-14 08:27:00
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
This is also an expensive layer. We might want to switch to setting up everything as root and switching to the APP_USER on startup using gosu.</pre>

<pre>item_index: 13
created_at: 2019-03-14 08:26:00
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
I believe this would need to happen in the same RUN instructions than the npm install to have effect on the final size</pre>

<pre>item_index: 14
created_at: 2019-03-14 08:10:36
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
use same indentation or fix the existing one</pre>

<pre>item_index: 15
created_at: 2019-03-13 12:07:22
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Unified dockerfile for easier building
body:
I need to have a closer look, but releasing a single image with that setup means that you are forced to use the all-in-one openproject docker image. While it is very nice for quick install, in production some people might want a separate container per service. This change will make that setup more complex for them.

I think there should be a way to override which services are launched by supervisord (e.g. an env variable interpreted in the entrypoint) so that one can choose to launch web, worker, db, etc. as separate processes. This will still make the image more heavy than what&#x27;s needed, but at least everyone is happy: we get a single image to maintain, and people can choose which processes supervisord launches.</pre>

<pre>item_index: 16
created_at: 2019-03-06 13:28:00
event_type: PullRequestEvent
repo_name: opf/openproject
title: Use latest buildpack with bundler2 support
body:
Build is in progress at https://packager.io/gh/crohr/openproject/builds/413/logs/sles-12

Will test and merge once ready.</pre>

<pre>item_index: 17
created_at: 2019-03-06 08:27:29
event_type: PullRequestEvent
repo_name: opf/openproject
title: Use latest buildpack with bundler2 support
body:
Build is in progress at https://packager.io/gh/crohr/openproject/builds/413/logs/sles-12

Will test and merge once ready.</pre>

<pre>item_index: 18
created_at: 2019-03-01 15:45:41
event_type: PullRequestEvent
repo_name: pkgr/addon-openproject
title: Install missing dependencies for fulltext search on Redhat/CentOS
body:
None</pre>

<pre>item_index: 19
created_at: 2019-03-01 15:26:53
event_type: PullRequestEvent
repo_name: opf/addon-openproject
title: Install node dependencies only when requested
body:
None</pre>

<pre>item_index: 20
created_at: 2019-03-01 15:26:49
event_type: IssueCommentEvent
repo_name: opf/addon-openproject
title: Install node dependencies only when requested
body:
@oliverguenther I&#x27;m going to merge this into master</pre>

<pre>item_index: 21
created_at: 2019-03-01 15:24:32
event_type: PullRequestEvent
repo_name: opf/addon-openproject
title: Install node dependencies only when requested
body:
None</pre>

<pre>item_index: 22
created_at: 2019-03-01 12:05:19
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Add custom getter for Setting.installation_uuid
body:
The new version now properly works on PullPreview</pre>

<pre>item_index: 23
created_at: 2019-03-01 11:13:48
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Add custom getter for Setting.installation_uuid
body:
@oliverguenther thanks, and also: testing it on PullPreview the UUID is again not properly set. </pre>

<pre>item_index: 24
created_at: 2019-03-01 08:26:17
event_type: PullRequestEvent
repo_name: opf/openproject
title: Add custom getter for Setting.installation_uuid
body:
This adds a custom getter for `Setting.installation_uuid`, so that we get more chances to generate a proper UUID for the installation.

Previously, it seems that the initializer could be called before the Settings table was available, which resulted, for some installations, in an empty installation_uuid being sent to the Release API.</pre>

<pre>item_index: 25
created_at: 2019-02-08 16:36:06
event_type: PullRequestEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
This uses the Release API to determine the status of the current OpenProject installation, and generate an SVG badge that is displayed in the admin block on the welcome page.

Available status:
* vulnerable
* unknown
* up to date
* update available

TODO:
- [x] update packager postinstall to set `OPENPROJECT_INSTALLATION__TYPE` to `packager`
- [x] send whether valid EE token in use</pre>

<pre>item_index: 26
created_at: 2019-02-08 08:26:55
event_type: PullRequestReviewCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
Thanks!</pre>

<pre>item_index: 27
created_at: 2019-02-07 16:44:20
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
Question: Do I need to update the country-specific locales? How does it work?</pre>

<pre>item_index: 28
created_at: 2019-02-07 15:41:50
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
@oliverguenther right, makes sense thanks</pre>

<pre>item_index: 29
created_at: 2019-02-07 14:53:01
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
This is what it looks like when put in the information admin panel:

&lt;img width=&quot;1154&quot; alt=&quot;image&quot; src=&quot;https://user-images.githubusercontent.com/6114/52419458-65cd9400-2af0-11e9-94dc-91c11dfacede.png&quot;&gt;
</pre>

<pre>item_index: 30
created_at: 2019-02-07 11:35:19
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
After some discussion, for this first pass we&#x27;ll display the badge on the admin block in the welcome page, and close to the version number in the admin section.

I&#x27;ll also alter the badge URL so that it sends the language currently used by the user, in case we want to generate language-aware badges later.</pre>

<pre>item_index: 31
created_at: 2019-02-07 10:36:16
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
I like the idea too, but that&#x27;s potentially two notification headers that get displayed, and then if snoozed or permanently hidden for that release, that installation goes missing in stats, and the user probably forgets to check the install status by other means.

I would be more inclined to display the badge on more pages, but only for admins.</pre>

<pre>item_index: 32
created_at: 2019-02-07 07:50:24
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
@oliverguenther thanks for the review, and yes this PR still needs:

* a way to update the security_badge_displayed boolean from the admin settings
* a change to our docker image and packages to set the `OPENPROJECT_INSTALLATION__TYPE` config value
* a few tests if possible</pre>

<pre>item_index: 33
created_at: 2019-02-06 11:09:10
event_type: PullRequestEvent
repo_name: opf/openproject
title: Display a security badge with the installation status
body:
This uses the Release API to determine the status of the current OpenProject installation, and generate an SVG badge that is displayed in the admin block on the welcome page.

Available status:
* vulnerable
* unknown
* up to date
* update available</pre>

<pre>item_index: 34
created_at: 2019-01-31 07:51:48
event_type: PullRequestEvent
repo_name: pkgr/gogs
title: Update to 0.11.79
body:
Update to 0.11.79 from gogs/gogs</pre>

<pre>item_index: 35
created_at: 2019-01-18 09:10:38
event_type: PullRequestEvent
repo_name: opf/openproject
title: Add dependencies required by the plaintext gem
body:
See https://github.com/planio-gmbh/plaintext.</pre>

<pre>item_index: 36
created_at: 2019-01-17 15:56:33
event_type: IssueCommentEvent
repo_name: opf/openproject
title: Add dependencies required by the plaintext gem
body:
Packages have been tested against all debian and ubuntu distributions. I will open a separate PR for CentOS support.</pre>

<pre>item_index: 37
created_at: 2019-01-17 11:14:01
event_type: PullRequestEvent
repo_name: opf/openproject
title: Add dependencies required by the plaintext gem
body:
See https://github.com/planio-gmbh/plaintext.

Please keep this PR open while I test a package build against it.</pre>

<pre>item_index: 38
created_at: 2019-01-09 07:51:25
event_type: IssueCommentEvent
repo_name: opf/openproject
title: [29288] Wait for postgres to start up in public image
body:
@oliverguenther maybe we can make the number of retries an env parameter with the default being 5?

@l0rn at the time this was written docker-compose was not in the same state as it is today, and having a single docker command to launch everything was pretty nice, especially since there are a few moving parts involved. Granted if this was to be done today we might go a different route.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      9,
      16,
      19,
      24,
      25,
      34,
      35
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      3,
      5,
      9,
      16,
      18,
      19,
      24,
      25,
      34,
      35
    ],
    &quot;description&quot;: &quot;Packaging and deployment infrastructure for OpenProject and related projects: unified Dockerfiles, buildpack updates, dependency management, Docker image optimization, and security badge features.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      10,
      11,
      12,
      13,
      20,
      28,
      32,
      38
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      7,
      16
    ],
    &quot;value&quot;: 1
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      16,
      18,
      19,
      24,
      25,
      34,
      35
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2,
      5,
      6,
      9,
      16,
      22,
      25,
      36
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      6,
      9,
      12,
      15,
      16,
      20,
      24,
      25,
      36
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 17: `armandofox` — `2013-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2013-06-19 15:21:24
event_type: PullRequestEvent
repo_name: saasbook/rag
title: Merge in HW3 &amp; HW4 support from richardxia/rag
body:
With this merge, saasbook/rag is capable of grading homeworks 1-4. Everything is working correctly as best as I can tell but please test it yourself. 

I don&#x27;t know what you (Richard) were trying to do with the whole misuse-FastReturn-as-goto whatever, but I have attempted to purge it because it was causing a merge conflict between richardxia/master and richardxia/feature-grader. I think I&#x27;ve merged it correctly (even if it is still ugly), but please take a look.

Additionally, I think we should either move hw3.yml, hw4.yml, and anything else that is relevant into the homework solutions repository or make this repository private.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;Autograder (rag) for SaaS course homeworks, extended to support grading homeworks 1-4&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 18: `bryanp` — `2011-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2011-12-22 04:52:06
event_type: PullRequestEvent
repo_name: metabahn/pakyow-auth
title: Added a summary to the gemspec.
body:
Gem and therefore bundler does not like the fact that there&#x27;s no summary in the gemspec. This pull just adds the summary field, therefore allowing bundler and gem to complete installation without warnings.</pre>

<pre>item_index: 2
created_at: 2011-12-16 03:17:53
event_type: IssueCommentEvent
repo_name: metabahn/pakyow-web
title: Fixing a Link
body:
Awesome, good catch.</pre>

<pre>item_index: 3
created_at: 2011-12-16 03:17:34
event_type: PullRequestEvent
repo_name: metabahn/pakyow-web
title: Fixing a Link
body:
Bryan,

I ran across a link in the routes section that looks like it points to the form[action] section from the old version of the site.  I pointed it to the right place if you want to merge it in.

My first contribution to pakyow! :)

~Wayne</pre>

<pre>item_index: 4
created_at: 2011-12-14 00:05:15
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Can&#x27;t use set_view and use_view_path at the same time.
body:
This is a non-issue since `set_view` and `use_view_path` aren&#x27;t designed to be used together. The `use_root_view_file` method should be used instead. Side note: better documentation is needed on the presenter api methods; some might even be combined or eliminated completely.</pre>

<pre>item_index: 5
created_at: 2011-12-14 00:05:15
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Can&#x27;t use set_view and use_view_path at the same time.
body:
This ability is needed in cases where we want to override the view path and root view from the backend. 

The `set_view` and `use_view_path` methods undo each other and can&#x27;t be used together (`set_view` sets `@view_path` to `nil` and `use_view_path` sets `@root_view_is_built` to `false`). Does  `set_view` need to reset `@view_path`? I can&#x27;t think of why it would, and if not, this is an easy fix.</pre>

<pre>item_index: 6
created_at: 2011-12-07 15:54:32
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binder &#x27;action&#x27; missing leading slash
body:
A fix will be included in the 0.7.1 release (due out in a week or so).</pre>

<pre>item_index: 7
created_at: 2011-12-01 16:33:06
event_type: PullRequestEvent
repo_name: nclaburn/curator
title: removed itemprops and added object type to name
body:
None</pre>

<pre>item_index: 8
created_at: 2011-11-08 19:32:49
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Post Config Block
body:
Realized you can do this by overloading the `initialize` method of `Application`:

```ruby
def initialize
  super
      
  # do post-load things here
end
```</pre>

<pre>item_index: 9
created_at: 2011-11-05 02:16:15
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binders should be able to modify attributes as well as replace them
body:
This is implemented as described here:

https://github.com/metabahn/pakyow/issues/10</pre>

<pre>item_index: 10
created_at: 2011-11-05 02:16:15
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Binders should be able to modify attributes as well as replace them
body:
Currently the Hash that a binder returns is used to supply new values for attributes of the tag being bound. We need to be able to have binders modify attributes is potentially arbitrary ways. Current thinking is to allow binders to be able to supply a lambda that would be called with the current attribute value and it&#x27;s return value will be used as the new value. This might have some synergy with the additional argument to `bind` to support general and nested hashes. </pre>

<pre>item_index: 11
created_at: 2011-11-05 02:15:40
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Appending Attribute Values
body:
It is possible to get/set the value of an attribute, but appending does not work (with &lt;&lt; or +=). One solution is to create a new Attribute class that subclasses String and does the right thing when appending a value.</pre>

<pre>item_index: 12
created_at: 2011-11-05 02:15:39
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Appending Attribute Values
body:
This is now implemented and merged into release. Existing attribute values can be modified with a lambda:

```ruby
presenter.view.find(&#x27;thing&#x27;).attributes.class = lambda { |current_class| current_class &lt;&lt; &#x27;foo&#x27; }
```

The return value will be the new attribute value. This is also true in binders:

```ruby
{ :class =&gt; lambda { |current_class| current_class &lt;&lt; &#x27;foo&#x27; } }
```

Attributes can be removed by setting the value to nil.</pre>

<pre>item_index: 13
created_at: 2011-11-03 21:57:43
event_type: PullRequestEvent
repo_name: metabahn/pakyow
title: I wrote a test for binding of view
body:
I think the pakyow need more tests.</pre>

<pre>item_index: 14
created_at: 2011-11-03 20:19:03
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Invoking Route or Error Handler
body:
Invoking the default route doesn&#x27;t seem to work. Given this route:

```ruby
default do
  Log.enter &quot;This is the default route&quot;
end
```

I would think it should be invokable as:

```ruby
app.invoke_route(&#x27;/&#x27;)
```

But, this doesn&#x27;t seem to work.</pre>

<pre>item_index: 15
created_at: 2011-11-03 19:27:32
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Invoking Route or Error Handler
body:
Confirmed that commenting out line 268 solves the problem, but not sure if this is the correct solution. Thoughts?</pre>

<pre>item_index: 16
created_at: 2011-11-03 19:22:47
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Invoking Route or Error Handler
body:
Another issue. When calling `app.redirect_to` an exception is thrown:

```
[500] uncaught throw :halt

/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/application.rb:268:in `throw&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/application.rb:268:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/reloader.rb:9:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/logger.rb:15:in `block in call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/logger.rb:14:in `catch&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/logger.rb:14:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/bundler/gems/pakyow-bd20d2a7b577/pakyow-core/lib/core/static.rb:15:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/gems/rack-1.3.5/lib/rack/session/abstract/id.rb:195:in `context&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/gems/rack-1.3.5/lib/rack/session/abstract/id.rb:190:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p290/lib/ruby/gems/1.9.1/gems/rack-1.3.5/lib/rack/methodoverride.rb:24:in `call&#x27;
/Users/bryan/.rbenv/versions/1.9.2-p</pre>

<pre>item_index: 17
created_at: 2011-11-03 18:40:31
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Invoking Route or Error Handler
body:
After playing around with this a bit I found a couple of things. 

First, should we make `method` optional and set it to the current request&#x27;s method by default?

Second, you currently have to enter the route exactly as it&#x27;s defined. So if my route is `/foo/bar` invoking `foo/bar` doesn&#x27;t work. Not sure the best way to handle this, but I think it would be nice for it not to matter.</pre>

<pre>item_index: 18
created_at: 2011-11-03 15:38:20
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Post Config Block
body:
I&#x27;ve run into a case where I need to execute some code when the server starts, but after the files in `lib` have been loaded. The only way to do this currently is to put it in the `routes` block. But surely there&#x27;s a better way.</pre>

<pre>item_index: 19
created_at: 2011-11-03 15:24:05
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: rbenv not installing bin/pakyow
body:
Not sure if this is an issue with rbenv or pakyow, but not having this trouble with other gems.</pre>

<pre>item_index: 20
created_at: 2011-11-03 03:11:52
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: 404 Unless Route Defined
body:
I wanted to get this down since it keeps coming up in conversations. This is the question of should the response succeed or not if a view directory exists but a route does not. The more I think about this the more I think a config option is needed that allows this behavior to be turned on or off. There are times in production where it would be nice to have.

This also brings up another potential issue with restful routes. What if a particular restful resource only implements part of the rest specification (e.g. new/create but not delete)? Perhaps there should be a better way of saying what parts of rest you want for a particular resource.</pre>

<pre>item_index: 21
created_at: 2011-11-03 03:08:09
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: [pakyow-core] Routing misbehavior
body:
Having only the following routes defined:

    default :ApplicationController, :index
    post &#x27;messages&#x27;    , :MessagesController, :create


When I make a `get` request to `/messages`
I get the following server response:

    Processing /messages (127.0.0.1 at 2011-08-29 10:37:30 -0300) [GET]
    Completed in 4.356622695922852ms | 200 | [http://localhost:3000/messages]

Then the `ApplicationController` `index` gets rendered on the browser. 

(Will try to create a test for this and hopefully a patch, I need to inspect the `pakyow-core/lib/core/route_store.rb` a little closer )

I also have an `app/views/messages/` directory.
</pre>

<pre>item_index: 22
created_at: 2011-11-03 03:03:26
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Route Aliases
body:
I ran into an instance today where it would be nice if in the route specification I could create aliases. For example:

```ruby
restful &#x27;/sessions&#x27;
alias &#x27;/logout&#x27;, &#x27;/sessions/destroy&#x27;
```

0.7 will kind of support this with `invoke_route`, but I wonder if there&#x27;s a benefit to adding this into the route specification language as well.</pre>

<pre>item_index: 23
created_at: 2011-11-03 02:55:51
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Restful Routes Without a Controller
body:
I realized tonight that there is no way to define restful routes without a controller. Here&#x27;s a possible way this could work (the syntax may be stupid, I spent all of five minutes on this):

```ruby
restful &#x27;/users&#x27; {
  index { ... }
  new { ... }
  create { ... }
  edit { ... }
  update { ... }
  delete { ... }
}
```</pre>

<pre>item_index: 24
created_at: 2011-10-28 22:14:20
event_type: IssuesEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
Would be nice to be able to bind nested hashes. For example:

```ruby
{ :contact =&gt; { :name =&gt; &#x27;John Doe&#x27; } }
```

Would bind to...

```html
&lt;span itemprop=&quot;contact[name]&quot;&gt;John Doe&lt;/span&gt;
```</pre>

<pre>item_index: 25
created_at: 2011-10-28 22:14:19
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
Just pushed some changes that bring clarity to binding. 

Support for wildcard itemprop types has been removed. 

Also, a subtle but very profound change has been made to how data is bound as a type. This is how it was implemented:

```ruby
view.bind(x, :as =&gt; :MyDataType)
```

And the syntax has changed to:

```ruby
view.bind(x, :to =&gt; :my_data_type)
```

Instead of saying what type the data should be bound as, we say where the data should be bound to. In this case the data would be bound properly to data labels defined like this:

```html
&lt;div itemprop=&quot;my_data_type[some_attribute]&quot;&gt;
  ...
&lt;/div&gt;
```

The same change has been made to binders. Instead of saying:

```ruby
binder_for :MyDataType
```

You now say:

```ruby
binder_for :my_data_type
```

This sets things up for a more functional system where data is not represented by models, but instead by primitive data structures (Arrays and Hashes). 

These changes have been merged into release.</pre>

<pre>item_index: 26
created_at: 2011-10-28 21:38:56
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Child to Parent
body:
Just as I can do this:

```ruby
dataset do
  User.constrain(:email).seed({
    :email =&gt; &#x27;john@gmail.com&#x27;,
    :password =&gt; &#x27;test&#x27;,
    :password_confirmation =&gt; &#x27;test&#x27;,
    :name =&gt; &#x27;John Doe&#x27;,
    :statuses =&gt; [0]
  })

  Status.seed({
    :text =&gt; &#x27;foo&#x27;
  })
end
```

This should also work:

```ruby
dataset do
  User.constrain(:email).seed({
    :email =&gt; &#x27;john@gmail.com&#x27;,
    :password =&gt; &#x27;test&#x27;,
    :password_confirmation =&gt; &#x27;test&#x27;,
    :name =&gt; &#x27;John Doe&#x27;
  })

  Status.seed({
    :text =&gt; &#x27;foo&#x27;,
    :user =&gt; 0
  })
end
```</pre>

<pre>item_index: 27
created_at: 2011-10-28 20:40:53
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Associated Objects Duplicated
body:
I have this dataset:

```ruby
dataset do
  User.constrain(:email).seed({
    :email =&gt; &#x27;john@gmail.com&#x27;,
    :password =&gt; &#x27;test&#x27;,
    :password_confirmation =&gt; &#x27;test&#x27;,
    :name =&gt; &#x27;John Doe&#x27;,
    :statuses =&gt; [0]
  })

  Status.seed({
    :text =&gt; &#x27;foo&#x27;
  })
end
```

A status is created each time. I understand why (the status isn&#x27;t constrained), but am trying to think of a way around this. In this particular case I don&#x27;t want a new status created for this user every time. Is there a way to constrain the status seed so that it&#x27;s only created once here?</pre>

<pre>item_index: 28
created_at: 2011-10-28 20:35:08
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Associations
body:
Two objects can be associated by using the associated object&#x27;s index, or an instance of the object. For example, this associates the `Comment` at index `0` in the current dataset with the `Post`:

```ruby
Post.seed({
  :comments =&gt; [0]
})
```

However, this should also work:

```ruby
Post.seed({
  :comments =&gt; [Comment.seed]
})
```</pre>

<pre>item_index: 29
created_at: 2011-10-26 16:39:38
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
Went ahead and pushed some code that invokes binders for hashes. For now I&#x27;ll hold off on removing support for wildcard itemprops.</pre>

<pre>item_index: 30
created_at: 2011-10-26 13:39:36
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
One more thing. I don&#x27;t think we need the ability to define wildcard itemprop values. We give the programmer the ability to bind an object as any type, and adding ambiguity on the frontend doesn&#x27;t seem necessary. It isn&#x27;t meaningful at all to look at HTML and see that it can be an object of any type.

This also could come into play with pakyow-ui, where in a lot of cases type will be important.</pre>

<pre>item_index: 31
created_at: 2011-10-26 12:39:31
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
I had forgotten that you treat a Resource in DataMapper as if it was a Hash. So if we have a model `User` with an attribute `email` we can access that data a couple of ways:

```ruby
u = User.get(1)
u.email
u[:email]
u[&#x27;email]
```

I believe you can do the same thing with ActiveRecord. Since access can be consistent in at least some cases I&#x27;m now thinking we should invoke binders with hashes or objects. There is probably still a better solution but this would keep things more consistent for 0.7.

Thoughts?</pre>

<pre>item_index: 32
created_at: 2011-10-25 22:41:59
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
Number one ended up being easiest, so that&#x27;s what I did for now. This is now working (pushed to the &#x27;binding&#x27; branch). Unless we want binders to be used when binding hashes, this is ready to be merged into release.</pre>

<pre>item_index: 33
created_at: 2011-10-25 22:22:44
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
So I assumed that when binding a hash as another object, the binder would be used if it exists for the object type. The thing is the code in the binder can&#x27;t be consistent since `bindable` can be a hash or an object. Seems we have two options:

1. Don&#x27;t use binders when binding a hash.
2. Pass a Bindable object to the binder method that can be treated the same way regardless of if a hash or other object is being bound.

Thoughts?</pre>

<pre>item_index: 34
created_at: 2011-10-25 22:03:23
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Datasets
body:
Datasets allow seeds to be grouped (each group has unique indices). Example:

```ruby
dataset :first do
  ...
end
```</pre>

<pre>item_index: 35
created_at: 2011-10-25 20:18:30
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Migrations
body:
A migration is needed in the event that the data for a constraint field changes. Here&#x27;s the proposed syntax:

```ruby
Post.seed(:title, {
  :title =&gt; [&#x27;Title 1&#x27;, &#x27;Title 2&#x27;],
  :body =&gt; &#x27;foo&#x27;
})
```</pre>

<pre>item_index: 36
created_at: 2011-10-25 20:18:30
event_type: IssuesEvent
repo_name: metabahn/farmer_john
title: Seed Definitions
body:
Definitions can be created that describe values for certain object types. Some examples:

```ruby
# create a default user definition
#
User.define {
  :email =&gt; lambda { gen_rand_email }
}

# seed a single user from default definition
#
User.seed

# create a named user definition
#
User.define(:bryan) {
  :email =&gt; &#x27;bryan@metabahn.com&#x27;
}

# seed a single user from a particular definition
#
User.seed(:bryan)
```</pre>

<pre>item_index: 37
created_at: 2011-10-25 14:18:16
event_type: IssueCommentEvent
repo_name: metabahn/farmer_john
title: Associations
body:
References to the associated object are passed in. The reference can be the object&#x27;s index in the dataset, or the actual object in memory. For has many relationships it would be an array of references, but for has one it would be a single reference.</pre>

<pre>item_index: 38
created_at: 2011-10-25 13:45:22
event_type: IssueCommentEvent
repo_name: metabahn/farmer_john
title: Seed Definitions
body:
Yep, that&#x27;s how I would expect it to work.</pre>

<pre>item_index: 39
created_at: 2011-10-24 19:42:04
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Binding Nested Hashes
body:
Based on today&#x27;s discussion binding will be changed to support the following syntaxes:

```html
itemprop=&quot;contact[name]&quot;
```

```html
itemprop=&quot;*[name]&quot;
```

Defining itemprops as just a key will no longer be supported.

Binding hashes will be supported like this:

```ruby
view.bind({ :name =&gt; &#x27;John Doe&#x27; }, :as =&gt; :Contact)
```</pre>

<pre>item_index: 40
created_at: 2011-10-19 22:20:40
event_type: IssueCommentEvent
repo_name: metabahn/pakyow
title: Before/After Hooks
body:
I think we should do this starting with the 0.7 release. Maybe a post summarizing things for the next major point release. We could even have release candidates to get feedback on implemented features. The more involvement the better. </pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      6,
      13,
      20,
      22,
      23,
      24
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      4,
      5,
      6,
      9,
      10,
      13,
      20,
      21,
      22,
      23,
      24,
      25,
      34,
      35,
      36,
      40
    ],
    &quot;description&quot;: &quot;Active development of the Pakyow Ruby web framework, including routing, view binding, gemspec management, datasets, migrations, and release planning.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      6,
      8,
      9,
      12,
      25,
      29,
      32,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      6,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      6,
      13,
      20,
      24,
      34,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      6,
      40
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      6,
      9,
      12,
      25,
      29,
      32,
      34,
      35,
      36,
      39,
      40
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 19: `davidhu2000` — `2022-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2022-12-20 18:25:58
event_type: IssuesEvent
repo_name: siimon/prom-client
title: filter out http_request_duration_seconds and http_requests_total? 
body:
we have an API that look something like 

```
/api/v1/blah/{id}/{type}
```

id - a number
type - a string

with 2 dynamic variables. but the metrics coming back doesn&#x27;t seem to parse the 2nd variable as a variable, but rather as a string

so we see stuff like

```
http_request_duration_seconds_bucket{le=&quot;0.1&quot;,route=&quot;/api/v1/blah/#val/type-1&quot;,method=&quot;GET&quot;,status=&quot;2XX&quot;}
...
http_request_duration_seconds_bucket{le=&quot;0.1&quot;,route=&quot;/api/v1/blah/#val/type-2&quot;,method=&quot;GET&quot;,status=&quot;2XX&quot;}
```

this causes the metrics API  response time to skyrocket since there are tons of different types. Our payload size was a few MBs. 

So I was wondering whether we can remove those particular metrics as we use other means to measure them. 

IT does appear the #val replacement only happen for numbers. i tried locally to put `type` as number, and it is parsed as #val correctly. </pre>

<pre>item_index: 2
created_at: 2022-12-15 23:24:08
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: update read me formatting in background section
body:

# What changes are introduced?

# Any screenshots?
</pre>

<pre>item_index: 3
created_at: 2022-12-13 16:22:21
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: add coverage and .github folder to npmignore
body:
# What changes are introduced?

# Any screenshots?
</pre>

<pre>item_index: 4
created_at: 2022-12-13 16:10:15
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: add badges to readme
body:
# What changes are introduced?

# Any screenshots?
</pre>

<pre>item_index: 5
created_at: 2022-12-13 15:48:59
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: set yarn version, fix readme typos, add package.json metadata
body:
None</pre>

<pre>item_index: 6
created_at: 2022-12-13 15:47:35
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: set yarn version, fix readme typos, add package.json metadata
body:
None</pre>

<pre>item_index: 7
created_at: 2022-12-13 07:10:27
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: improve readme with import statement
body:
None</pre>

<pre>item_index: 8
created_at: 2022-12-13 07:10:21
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: chore: improve readme with import statement
body:
None</pre>

<pre>item_index: 9
created_at: 2022-12-13 07:06:01
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: fix: update tsconfig exclude to not include tests in build
body:
None</pre>

<pre>item_index: 10
created_at: 2022-12-13 07:05:45
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: fix: update tsconfig exclude to not include tests in build
body:
None</pre>

<pre>item_index: 11
created_at: 2022-12-13 07:01:11
event_type: PullRequestEvent
repo_name: davidhu2000/use-better-effect
title: fix: add prepublish script to build the code
body:
None</pre>

<pre>item_index: 12
created_at: 2022-12-10 04:40:49
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump prettier from 2.8.0 to 2.8.1
body:
Bumps [prettier](https://github.com/prettier/prettier) from 2.8.0 to 2.8.1.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/prettier/prettier/releases&quot;&gt;prettier&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;2.8.1&lt;/h2&gt;
&lt;p&gt;🔗 &lt;a href=&quot;https://github.com/prettier/prettier/blob/main/CHANGELOG.md#281&quot;&gt;Changelog&lt;/a&gt;&lt;/p&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/prettier/prettier/blob/main/CHANGELOG.md&quot;&gt;prettier&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h1&gt;2.8.1&lt;/h1&gt;
&lt;p&gt;&lt;a href=&quot;https://github.com/prettier/prettier/compare/2.8.0...2.8.1&quot;&gt;diff&lt;/a&gt;&lt;/p&gt;
&lt;h4&gt;Fix SCSS map in arguments (&lt;a href=&quot;https://github-redirect.dependabot.com/prettier/prettier/pull/9184&quot;&gt;#9184&lt;/a&gt; by &lt;a href=&quot;https://github.com/agamkrbit&quot;&gt;&lt;code&gt;@​agamkrbit&lt;/code&gt;&lt;/a&gt;)&lt;/h4&gt;
&lt;!-- raw HTML omitted --&gt;
&lt;pre lang=&quot;scss&quot;&gt;&lt;code&gt;// Input
$display-breakpoints: map-deep-merge(
  (
    &amp;quot;print-only&amp;quot;: &amp;quot;only print&amp;quot;,
    &amp;quot;screen-only&amp;quot;: &amp;quot;only screen&amp;quot;,
    &amp;quot;xs-only&amp;quot;: &amp;quot;only screen and (max-width: #{map-get($grid-breakpoints, &amp;quot;sm&amp;quot;)-1})&amp;quot;,
  ),
  $display-breakpoints
);
&lt;p&gt;// Prettier 2.8.0
$display-breakpoints: map-deep-merge(
(
&amp;quot;print-only&amp;quot;: &amp;quot;only print&amp;quot;,
&amp;quot;screen-only&amp;quot;: &amp;quot;only screen&amp;quot;,
&amp;quot;xs-only&amp;quot;: &amp;quot;only screen and (max-width: #{map-get($grid-breakpoints, &amp;quot; sm
&amp;quot;)-1})&amp;quot;,
),
$display-breakpoi</pre>

<pre>item_index: 13
created_at: 2022-12-08 06:07:11
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: fix: add language to code blocks to fix theme toggle
body:
without a language, the dark/light theme doesn&#x27;t apply properly. So adding one so it shows up correctly </pre>

<pre>item_index: 14
created_at: 2022-12-08 06:05:34
event_type: IssuesEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Recommended section title should be center aligned
body:
![image](https://user-images.githubusercontent.com/15827041/204859040-2c100983-ca7f-40b0-b80a-56af789e6f3f.png)</pre>

<pre>item_index: 15
created_at: 2022-12-08 06:05:33
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: fix: update title to be center aligned on blog recommend section
body:
fixes #78</pre>

<pre>item_index: 16
created_at: 2022-12-08 06:03:43
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: fix: update title to be center aligned on blog recommend section
body:
fixes #78</pre>

<pre>item_index: 17
created_at: 2022-12-08 06:01:19
event_type: IssuesEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Menu bar not visible on mobile
body:
![image](https://user-images.githubusercontent.com/15827041/204858864-f6104f28-17a8-4b54-a18c-017a48e1f042.png)</pre>

<pre>item_index: 18
created_at: 2022-12-08 06:01:19
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: fix: update mobile menu text to be visible
body:
fixes #77 </pre>

<pre>item_index: 19
created_at: 2022-12-08 04:45:46
event_type: PullRequestEvent
repo_name: davidhu2000/react-spinners
title: chore: update devDependencies to latest versions
body:
# What changes are introduced?

# Any screenshots?
</pre>

<pre>item_index: 20
created_at: 2022-12-06 20:16:31
event_type: IssuesEvent
repo_name: davidhu2000/react-spinners
title: Update colors prop to validate using typings
body:
Currently, the cooor prop runs through a custom function that validates the color is valid. Maybe worth looking into if we can utilize the css typings to auto verify it.</pre>

<pre>item_index: 21
created_at: 2022-12-03 06:20:55
event_type: PullRequestEvent
repo_name: davidhu2000/react-spinners
title: chore: update devDependencies to latest versions
body:
# What changes are introduced?

# Any screenshots?
</pre>

<pre>item_index: 22
created_at: 2022-12-03 06:12:37
event_type: PullRequestEvent
repo_name: davidhu2000/react-spinners
title: Bump decode-uri-component from 0.2.0 to 0.2.2
body:
Bumps [decode-uri-component](https://github.com/SamVerschueren/decode-uri-component) from 0.2.0 to 0.2.2.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/SamVerschueren/decode-uri-component/releases&quot;&gt;decode-uri-component&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;v0.2.2&lt;/h2&gt;
&lt;ul&gt;
&lt;li&gt;Prevent overwriting previously decoded tokens  980e0bf&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;&lt;a href=&quot;https://github.com/SamVerschueren/decode-uri-component/compare/v0.2.1...v0.2.2&quot;&gt;https://github.com/SamVerschueren/decode-uri-component/compare/v0.2.1...v0.2.2&lt;/a&gt;&lt;/p&gt;
&lt;h2&gt;v0.2.1&lt;/h2&gt;
&lt;ul&gt;
&lt;li&gt;Switch to GitHub workflows  76abc93&lt;/li&gt;
&lt;li&gt;Fix issue where decode throws - fixes &lt;a href=&quot;https://github-redirect.dependabot.com/SamVerschueren/decode-uri-component/issues/6&quot;&gt;#6&lt;/a&gt;  746ca5d&lt;/li&gt;
&lt;li&gt;Update license (&lt;a href=&quot;https://github-redirect.dependabot.com/SamVerschueren/decode-uri-component/issues/1&quot;&gt;#1&lt;/a&gt;)  486d7e2&lt;/li&gt;
&lt;li&gt;Tidelift tasks  a650457&lt;/li&gt;
&lt;li&gt;Meta tweaks  66e1c28&lt;/li&gt;
&lt;/ul&gt;
&lt;p&gt;&lt;a href=&quot;https://github.com/SamVerschueren/decode-uri-component/compare/v0.2.0...v0.2.1&quot;&gt;https://github.com/SamVerschueren/decode-uri-component/compare/v0.2.0...v0.2.1&lt;/a&gt;&lt;/p&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/SamVerschueren/decode-uri-component/commit/a0eea469d26eb0df668b081672cdb9581feb78eb&quot;&gt;&lt;code&gt;a0eea46&lt;/code&gt;&lt;/a&gt; 0.2.2&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/SamVerschueren/decode-uri-component/commit/980e0bf09b64d94f1aa79012f8</pre>

<pre>item_index: 23
created_at: 2022-12-03 06:04:19
event_type: IssueCommentEvent
repo_name: davidhu2000/react-spinners
title: Pacman Loader overlaps with other content
body:
@bsgriggs PacmanLoader is fixed in 0.13.7 based on your recommendation, still need to look into the other 3. </pre>

<pre>item_index: 24
created_at: 2022-12-01 02:23:53
event_type: IssuesEvent
repo_name: luin/ioredis
title: Mismatch types in set vs get
body:
Looks like `set` allows the value to be `number | string`, but `get` only returns string

```ts
RedisCommander&lt;{ type: &quot;default&quot;; }&gt;.set(key: RedisKey, value: string | number | Buffer, callback?: Callback&lt;&quot;OK&quot;&gt; | undefined): Promise&lt;&quot;OK&quot;&gt;
RedisCommander&lt;{ type: &quot;default&quot;; }&gt;.get(key: RedisKey, callback?: Callback&lt;string | null&gt; | undefined): Promise&lt;string | null&gt;
```

a simple repro

```ts
import Redis from &#x27;ioredis&#x27;;

const redis = new Redis({
  password: process.env.REDIS_PASSWORD,
  host: process.env.REDIS_HOST,
});

redis.set(&#x27;key&#x27;, 1);
redis.set(&#x27;key&#x27;, &#x27;hi&#x27;);

const value = await redis.get(&#x27;key&#x27;); // value is string | null
```

I think set and get should match in type, so get should also be returning type number. 

ioredis 5.2.4

I think generics would be great to use here. So when I initialize Redis, I can set a type. for example 

```ts
const redis = new Redis&lt;string&gt;({});
const redis = new Redis&lt;number&gt;({});
```</pre>

<pre>item_index: 25
created_at: 2022-11-30 20:05:04
event_type: IssueCommentEvent
repo_name: luin/ioredis
title: Mismatch types in set vs get
body:
```
127.0.0.1:6379&gt; set key 1
OK
127.0.0.1:6379&gt; get key
&quot;1&quot;
```

learn something new every day. It&#x27;s all just strings so the type is correct. Altho now I&#x27;m wondering if the `set` function shouldn&#x27;t take number so get/set still match. </pre>

<pre>item_index: 26
created_at: 2022-11-30 19:52:08
event_type: IssuesEvent
repo_name: luin/ioredis
title: Mismatch types in set vs get
body:
Looks like `set` allows the value to be `number | string`, but `get` only returns string

```ts
RedisCommander&lt;{ type: &quot;default&quot;; }&gt;.set(key: RedisKey, value: string | number | Buffer, callback?: Callback&lt;&quot;OK&quot;&gt; | undefined): Promise&lt;&quot;OK&quot;&gt;
RedisCommander&lt;{ type: &quot;default&quot;; }&gt;.get(key: RedisKey, callback?: Callback&lt;string | null&gt; | undefined): Promise&lt;string | null&gt;
```

a simple repro

```ts
import Redis from &#x27;ioredis&#x27;;

const redis = new Redis({
  password: process.env.REDIS_PASSWORD,
  host: process.env.REDIS_HOST,
});

redis.set(&#x27;key&#x27;, 1);
redis.set(&#x27;key&#x27;, &#x27;hi&#x27;);

const value = await redis.get(&#x27;key&#x27;); // value is string | null
```

I think set and get should match in type, so get should also be returning type number. 

ioredis 5.2.4

I think generics would be great to use here. So when I initialize Redis, I can set a type. for example 

```ts
const redis = new Redis&lt;string&gt;({});
const redis = new Redis&lt;number&gt;({});
```</pre>

<pre>item_index: 27
created_at: 2022-11-30 16:52:30
event_type: IssuesEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Recommended section title should be center aligned
body:
![image](https://user-images.githubusercontent.com/15827041/204859040-2c100983-ca7f-40b0-b80a-56af789e6f3f.png)</pre>

<pre>item_index: 28
created_at: 2022-11-30 16:51:36
event_type: IssuesEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Menu bar not visible on mobile
body:
![image](https://user-images.githubusercontent.com/15827041/204858864-f6104f28-17a8-4b54-a18c-017a48e1f042.png)</pre>

<pre>item_index: 29
created_at: 2022-11-28 05:29:16
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @astrojs/mdx from 0.11.4 to 0.12.0
body:
Bumps [@astrojs/mdx](https://github.com/withastro/astro/tree/HEAD/packages/integrations/mdx) from 0.11.4 to 0.12.0.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/releases&quot;&gt;&lt;code&gt;@​astrojs/mdx&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/mdx&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.12.0&lt;/h2&gt;
&lt;h3&gt;Minor Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5427&quot;&gt;#5427&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/2a1c085b199f24e34424ec8c19041c03602c53c5&quot;&gt;&lt;code&gt;2a1c085b1&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/backflip&quot;&gt;&lt;code&gt;@​backflip&lt;/code&gt;&lt;/a&gt;! - Uses remark-rehype options from astro.config.mjs&lt;/li&gt;
&lt;/ul&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5448&quot;&gt;#5448&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/ef2ffc7ae9ff554860238ecd2fb3bf6d82b5801b&quot;&gt;&lt;code&gt;ef2ffc7ae&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/delucis&quot;&gt;&lt;code&gt;@​delucis&lt;/code&gt;&lt;/a&gt;! - Fix broken link in README&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/mdx&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.11.6&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5335&quot;&gt;#5335&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/dca762cf734a657d8f126fd6958892b6163a4f67&quot;&gt;&lt;code&gt;dca762cf7&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/bluwy&quot;&gt;&lt;cod</pre>

<pre>item_index: 30
created_at: 2022-11-28 05:27:43
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump astro-icon from 0.7.3 to 0.8.0
body:
Bumps [astro-icon](https://github.com/natemoo-re/astro-icon/tree/HEAD/packages/core) from 0.7.3 to 0.8.0.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/natemoo-re/astro-icon/releases&quot;&gt;astro-icon&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;astro-icon@0.8.0&lt;/h2&gt;
&lt;h3&gt;Minor Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/natemoo-re/astro-icon/pull/42&quot;&gt;#42&lt;/a&gt; &lt;a href=&quot;https://github.com/natemoo-re/astro-icon/commit/ae0a7f72358dee39a133663423b499e4525c06cb&quot;&gt;&lt;code&gt;ae0a7f7&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/germanz&quot;&gt;&lt;code&gt;@​germanz&lt;/code&gt;&lt;/a&gt;! - Pass props to custom resolvers&lt;/li&gt;
&lt;/ul&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;
&lt;p&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/natemoo-re/astro-icon/pull/56&quot;&gt;#56&lt;/a&gt; &lt;a href=&quot;https://github.com/natemoo-re/astro-icon/commit/60c7304368a7ca88fa2190bc8bfac5e8229e0f50&quot;&gt;&lt;code&gt;60c7304&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/dwightjack&quot;&gt;&lt;code&gt;@​dwightjack&lt;/code&gt;&lt;/a&gt;! - Fix Chrome not rendering icons using SVG gradients&lt;/p&gt;
&lt;/li&gt;
&lt;li&gt;
&lt;p&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/natemoo-re/astro-icon/pull/64&quot;&gt;#64&lt;/a&gt; &lt;a href=&quot;https://github.com/natemoo-re/astro-icon/commit/2c75a4a6bc675492bee96aeac89c05f610f28831&quot;&gt;&lt;code&gt;2c75a4a&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/stramel&quot;&gt;&lt;code&gt;@​stramel&lt;/code&gt;&lt;/a&gt;! - Update Sprite context to track usages using &lt;code&gt;Astro.request&lt;/code&gt;&lt;/p&gt;
&lt;/li&gt;
&lt;li&gt;
&lt;p&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/natemoo-re/as</pre>

<pre>item_index: 31
created_at: 2022-11-28 05:27:06
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump tailwindcss from 3.1.8 to 3.2.4
body:
Bumps [tailwindcss](https://github.com/tailwindlabs/tailwindcss) from 3.1.8 to 3.2.4.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/tailwindlabs/tailwindcss/releases&quot;&gt;tailwindcss&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;v3.2.4&lt;/h2&gt;
&lt;h3&gt;Added&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Add &lt;code&gt;blocklist&lt;/code&gt; option to prevent generating unwanted CSS (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9812&quot;&gt;#9812&lt;/a&gt;)&lt;/li&gt;
&lt;/ul&gt;
&lt;h3&gt;Fixed&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Fix watching of files on Linux when renames are involved (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9796&quot;&gt;#9796&lt;/a&gt;)&lt;/li&gt;
&lt;li&gt;Make sure errors are always displayed when watching for changes (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9810&quot;&gt;#9810&lt;/a&gt;)&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;v3.2.3&lt;/h2&gt;
&lt;h3&gt;Fixed&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Fixed use of &lt;code&gt;raw&lt;/code&gt; content in the CLI (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9773&quot;&gt;#9773&lt;/a&gt;)&lt;/li&gt;
&lt;li&gt;Pick up changes from files that are both context and content deps (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9787&quot;&gt;#9787&lt;/a&gt;)&lt;/li&gt;
&lt;li&gt;Sort pseudo-elements ONLY after classes when using variants and &lt;code&gt;@apply&lt;/code&gt; (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss/pull/9765&quot;&gt;#9765&lt;/a&gt;)&lt;/li&gt;
&lt;li&gt;Support important utilities in the safelist (pattern must include a &lt;code&gt;!&lt;/code&gt;) (&lt;a href=&quot;https://github-re</pre>

<pre>item_index: 32
created_at: 2022-11-28 05:26:10
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @astrojs/rss from 1.0.2 to 1.0.3
body:
Bumps [@astrojs/rss](https://github.com/withastro/astro/tree/HEAD/packages/astro-rss) from 1.0.2 to 1.0.3.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/releases&quot;&gt;&lt;code&gt;@​astrojs/rss&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/rss&lt;/code&gt;&lt;a href=&quot;https://github.com/1&quot;&gt;&lt;code&gt;@​1&lt;/code&gt;&lt;/a&gt;.0.3&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5164&quot;&gt;#5164&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/4a8a346ca9a6d6ed8def2fa32329c1db922893d2&quot;&gt;&lt;code&gt;4a8a346ca&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/MoustaphaDev&quot;&gt;&lt;code&gt;@​MoustaphaDev&lt;/code&gt;&lt;/a&gt;! - Add support for markdown files with the following extensions:
&lt;ul&gt;
&lt;li&gt;&lt;code&gt;.markdown&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;code&gt;.mdown&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;code&gt;.mkdn&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;code&gt;.mkd&lt;/code&gt;&lt;/li&gt;
&lt;li&gt;&lt;code&gt;.mdwn&lt;/code&gt;&lt;/li&gt;
&lt;/ul&gt;
&lt;/li&gt;
&lt;/ul&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/blob/main/packages/astro-rss/CHANGELOG.md&quot;&gt;&lt;code&gt;@​astrojs/rss&lt;/code&gt;&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;1.0.3&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5164&quot;&gt;#5164&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/4a8a346ca9a6d6ed8def2fa32329c1db922893d2&quot;&gt;&lt;code&gt;4a8a346ca&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/MoustaphaDev&quot;&gt;&lt;code&gt;@​MoustaphaDev</pre>

<pre>item_index: 33
created_at: 2022-11-28 05:25:54
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @astrojs/tailwind from 2.0.2 to 2.1.3
body:
Bumps [@astrojs/tailwind](https://github.com/withastro/astro/tree/HEAD/packages/integrations/tailwind) from 2.0.2 to 2.1.3.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/releases&quot;&gt;&lt;code&gt;@​astrojs/tailwind&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/tailwind&lt;/code&gt;&lt;a href=&quot;https://github.com/2&quot;&gt;&lt;code&gt;@​2&lt;/code&gt;&lt;/a&gt;.1.3&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5450&quot;&gt;#5450&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/cef33dd841b7d4d9437efac54f7e185a40cc3d4b&quot;&gt;&lt;code&gt;cef33dd84&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/chenxsan&quot;&gt;&lt;code&gt;@​chenxsan&lt;/code&gt;&lt;/a&gt;! - Remove temp tailwind config file in finally&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/tailwind&lt;/code&gt;&lt;a href=&quot;https://github.com/2&quot;&gt;&lt;code&gt;@​2&lt;/code&gt;&lt;/a&gt;.1.2&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5270&quot;&gt;#5270&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/bb6e8800094dc59841eb3b345fcb8baca9e17ce9&quot;&gt;&lt;code&gt;bb6e88000&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/matthewp&quot;&gt;&lt;code&gt;@​matthewp&lt;/code&gt;&lt;/a&gt;! - Prevent errors during HMR from crashing dev server&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/tailwind&lt;/code&gt;&lt;a href=&quot;https://github.com/2&quot;&gt;&lt;code&gt;@​2&lt;/code&gt;&lt;/a&gt;.1.1&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5082&quot;&gt;#5082&lt;/a&gt; &lt;a href=&quot;https://github</pre>

<pre>item_index: 34
created_at: 2022-11-28 05:22:15
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump prettier from 2.7.1 to 2.8.0
body:
Bumps [prettier](https://github.com/prettier/prettier) from 2.7.1 to 2.8.0.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/prettier/prettier/releases&quot;&gt;prettier&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;2.8.0&lt;/h2&gt;
&lt;p&gt;&lt;a href=&quot;https://github.com/prettier/prettier/compare/2.7.1...2.8.0&quot;&gt;diff&lt;/a&gt;&lt;/p&gt;
&lt;p&gt;🔗 &lt;a href=&quot;https://prettier.io/blog/2022/11/23/2.8.0.html&quot;&gt;Release note&lt;/a&gt;&lt;/p&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/prettier/prettier/blob/main/CHANGELOG.md&quot;&gt;prettier&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h1&gt;2.8.0&lt;/h1&gt;
&lt;p&gt;&lt;a href=&quot;https://github.com/prettier/prettier/compare/2.7.1...2.8.0&quot;&gt;diff&lt;/a&gt;&lt;/p&gt;
&lt;p&gt;🔗 &lt;a href=&quot;https://prettier.io/blog/2022/11/23/2.8.0.html&quot;&gt;Release Notes&lt;/a&gt;&lt;/p&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/prettier/prettier/commit/dcc0623911f8b352eda18f60683eb1a232d6c2bd&quot;&gt;&lt;code&gt;dcc0623&lt;/code&gt;&lt;/a&gt; Release 2.8.0&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/prettier/prettier/commit/7f7498109be4507662f03f930f2537f58b56d4b8&quot;&gt;&lt;code&gt;7f74981&lt;/code&gt;&lt;/a&gt; Remove version validattion temp&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/prettier/prettier/commit/876c297589ad9e3b6fea5214454a0f657e189eaf&quot;&gt;&lt;code&gt;876c297&lt;/code&gt;&lt;/a&gt; Update changelog for &lt;code&gt;satisfies&lt;/code&gt; (&lt;a href=&quot;https://github-redirect.dependabot.com/prettier/prettier/issues/13879&quot;&gt;#13879&lt;/a&gt;)&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/prettier/prett</pre>

<pre>item_index: 35
created_at: 2022-11-28 05:22:01
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @astrojs/image from 0.9.1 to 0.11.6
body:
Bumps [@astrojs/image](https://github.com/withastro/astro/tree/HEAD/packages/integrations/image) from 0.9.1 to 0.11.6.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/releases&quot;&gt;&lt;code&gt;@​astrojs/image&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/image&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.11.6&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5393&quot;&gt;#5393&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/e2fb0c4ff29d27bbd39193127c64fd4f312129e3&quot;&gt;&lt;code&gt;e2fb0c4ff&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/wulinsheng123&quot;&gt;&lt;code&gt;@​wulinsheng123&lt;/code&gt;&lt;/a&gt;! - Log error if failed to fetch remote image&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/image&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.11.5&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5361&quot;&gt;#5361&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/ee750087ce360c54d349f160d84bbdafb0ec83b4&quot;&gt;&lt;code&gt;ee750087c&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/matthewp&quot;&gt;&lt;code&gt;@​matthewp&lt;/code&gt;&lt;/a&gt;! - Allows &lt;code&gt;@​astrojs/image&lt;/code&gt; to be used in Vercel SSR&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/image&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.11.4&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5360&quot;&gt;#5360&lt;/a&gt; &lt;a href=&quot;https://</pre>

<pre>item_index: 36
created_at: 2022-11-28 05:17:49
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @tailwindcss/typography from 0.5.7 to 0.5.8
body:
Bumps [@tailwindcss/typography](https://github.com/tailwindcss/typography) from 0.5.7 to 0.5.8.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/tailwindcss/typography/releases&quot;&gt;&lt;code&gt;@​tailwindcss/typography&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;v0.5.8&lt;/h2&gt;
&lt;h3&gt;Fixed&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Fix selector when using a non-default class (e.g. &lt;code&gt;prose-sm&lt;/code&gt;) (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss-typography/pull/289&quot;&gt;#289&lt;/a&gt;)&lt;/li&gt;
&lt;/ul&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/tailwindlabs/tailwindcss-typography/blob/master/CHANGELOG.md&quot;&gt;&lt;code&gt;@​tailwindcss/typography&lt;/code&gt;&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;[0.5.8] - 2022-11-07&lt;/h2&gt;
&lt;h3&gt;Fixed&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;Fix selector when using a non-default class (e.g. &lt;code&gt;prose-sm&lt;/code&gt;) (&lt;a href=&quot;https://github-redirect.dependabot.com/tailwindlabs/tailwindcss-typography/pull/289&quot;&gt;#289&lt;/a&gt;)&lt;/li&gt;
&lt;/ul&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/tailwindlabs/tailwindcss-typography/commit/595ea7d618fe25e82010b7655aa37c36a484eafe&quot;&gt;&lt;code&gt;595ea7d&lt;/code&gt;&lt;/a&gt; 0.5.8&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/tailwindlabs/tailwindcss-typography/commit/e057044417e50e7a2c2d943e521648132d0c38e3&quot;&gt;&lt;code&gt;e057044&lt;/code&gt;&lt;/a&gt; Update changelog&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/tailwindlabs/tailwindcss-typography/commit/9999d2f4a69bd15798</pre>

<pre>item_index: 37
created_at: 2022-11-28 05:17:37
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump rehype-pretty-code from 0.3.2 to 0.5.1
body:
Bumps [rehype-pretty-code](https://github.com/atomiks/rehype-pretty-code) from 0.3.2 to 0.5.1.
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;See full diff in &lt;a href=&quot;https://github.com/atomiks/rehype-pretty-code/commits&quot;&gt;compare view&lt;/a&gt;&lt;/li&gt;
&lt;/ul&gt;
&lt;/details&gt;
&lt;br /&gt;


[![Dependabot compatibility score](https://dependabot-badges.githubapp.com/badges/compatibility_score?dependency-name=rehype-pretty-code&amp;package-manager=npm_and_yarn&amp;previous-version=0.3.2&amp;new-version=0.5.1)](https://docs.github.com/en/github/managing-security-vulnerabilities/about-dependabot-security-updates#about-compatibility-scores)

Dependabot will resolve any conflicts with this PR as long as you don&#x27;t alter it yourself. You can also trigger a rebase manually by commenting `@dependabot rebase`.

[//]: # (dependabot-automerge-start)
[//]: # (dependabot-automerge-end)

---

&lt;details&gt;
&lt;summary&gt;Dependabot commands and options&lt;/summary&gt;
&lt;br /&gt;

You can trigger Dependabot actions by commenting on this PR:
- `@dependabot rebase` will rebase this PR
- `@dependabot recreate` will recreate this PR, overwriting any edits that have been made to it
- `@dependabot merge` will merge this PR after your CI passes on it
- `@dependabot squash and merge` will squash and merge this PR after your CI passes on it
- `@dependabot cancel merge` will cancel a previously requested merge and block automerging
- `@dependabot reopen` will reopen this PR if it is closed
- `@dependabot close` will close this PR and stop Dependabot recrea</pre>

<pre>item_index: 38
created_at: 2022-11-28 05:13:20
event_type: IssueCommentEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @tailwindcss/typography from 0.5.7 to 0.5.8
body:
@dependabot rebas</pre>

<pre>item_index: 39
created_at: 2022-11-28 05:12:36
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump sharp from 0.31.1 to 0.31.2
body:
Bumps [sharp](https://github.com/lovell/sharp) from 0.31.1 to 0.31.2.
&lt;details&gt;
&lt;summary&gt;Changelog&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/lovell/sharp/blob/main/docs/changelog.md&quot;&gt;sharp&#x27;s changelog&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h3&gt;v0.31.2 - 4th November 2022&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;
&lt;p&gt;Upgrade to libvips v8.13.3 for upstream bug fixes.&lt;/p&gt;
&lt;/li&gt;
&lt;li&gt;
&lt;p&gt;Ensure manual flip, rotate, resize operation ordering (regression in 0.31.1)
&lt;a href=&quot;https://github-redirect.dependabot.com/lovell/sharp/issues/3391&quot;&gt;#3391&lt;/a&gt;&lt;/p&gt;
&lt;/li&gt;
&lt;li&gt;
&lt;p&gt;Ensure auto-rotation works without resize (regression in 0.31.1)
&lt;a href=&quot;https://github-redirect.dependabot.com/lovell/sharp/issues/3422&quot;&gt;#3422&lt;/a&gt;&lt;/p&gt;
&lt;/li&gt;
&lt;/ul&gt;
&lt;/blockquote&gt;
&lt;/details&gt;
&lt;details&gt;
&lt;summary&gt;Commits&lt;/summary&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/lovell/sharp/commit/9fa516e8496d96fc12a4cba25216e467e36d62b7&quot;&gt;&lt;code&gt;9fa516e&lt;/code&gt;&lt;/a&gt; Release v0.31.2&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/lovell/sharp/commit/12f472126dab042c60e5dda56c74a15cb371dea0&quot;&gt;&lt;code&gt;12f4721&lt;/code&gt;&lt;/a&gt; CI: Only pin Python version on x64 macOS and Windows&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/lovell/sharp/commit/18be09f1d70f85008684a259a2b9e1ea1bcf6d61&quot;&gt;&lt;code&gt;18be09f&lt;/code&gt;&lt;/a&gt; CI: Pin Python to 3.10&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/lovell/sharp/commit/b3c3290f903ae610d6d3ce6078cd849bc8230e8c&quot;&gt;&lt;code&gt;b3c3290&lt;/code&gt;&lt;/a&gt; Upgrade to libvips v8.13.3&lt;/li&gt;
&lt;li&gt;&lt;a href=&quot;https://github.com/lovell/sharp/commit/123f95c85a6a7c3e3e96fef6354e1f05857180d2&quot;&gt;&lt;code&gt;123f95c&lt;/co</pre>

<pre>item_index: 40
created_at: 2022-11-28 05:10:15
event_type: PullRequestEvent
repo_name: davidhu2000/davidhu2000.github.io
title: Bump @astrojs/prefetch from 0.0.7 to 0.1.1
body:
Bumps [@astrojs/prefetch](https://github.com/withastro/astro/tree/HEAD/packages/astro-prefetch) from 0.0.7 to 0.1.1.
&lt;details&gt;
&lt;summary&gt;Release notes&lt;/summary&gt;
&lt;p&gt;&lt;em&gt;Sourced from &lt;a href=&quot;https://github.com/withastro/astro/releases&quot;&gt;&lt;code&gt;@​astrojs/prefetch&lt;/code&gt;&#x27;s releases&lt;/a&gt;.&lt;/em&gt;&lt;/p&gt;
&lt;blockquote&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/prefetch&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.1.1&lt;/h2&gt;
&lt;h3&gt;Patch Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;
&lt;p&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5244&quot;&gt;#5244&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/6ad91bd80dae935b67a5c18b8dfbb95f2cfe10ef&quot;&gt;&lt;code&gt;6ad91bd80&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/deeprobin&quot;&gt;&lt;code&gt;@​deeprobin&lt;/code&gt;&lt;/a&gt;! - Do not prefetch if browser is offline or uses 3G&lt;/p&gt;
&lt;/li&gt;
&lt;li&gt;
&lt;p&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5271&quot;&gt;#5271&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/b6afe2c1db613aabf3139fb58e0fc2ab60322f37&quot;&gt;&lt;code&gt;b6afe2c1d&lt;/code&gt;&lt;/a&gt; Thanks &lt;a href=&quot;https://github.com/tony-sull&quot;&gt;&lt;code&gt;@​tony-sull&lt;/code&gt;&lt;/a&gt;! - Adds additional package.json keywords used for discoverability in the Integrations catalog&lt;/p&gt;
&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;&lt;code&gt;@​astrojs/prefetch&lt;/code&gt;&lt;a href=&quot;https://github.com/0&quot;&gt;&lt;code&gt;@​0&lt;/code&gt;&lt;/a&gt;.1.0&lt;/h2&gt;
&lt;h3&gt;Minor Changes&lt;/h3&gt;
&lt;ul&gt;
&lt;li&gt;&lt;a href=&quot;https://github-redirect.dependabot.com/withastro/astro/pull/5125&quot;&gt;#5125&lt;/a&gt; &lt;a href=&quot;https://github.com/withastro/astro/commit/5a674f976d6138ec5c87441a579c2ccf37713e73&quot;&gt;&lt;cod</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      7,
      11
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      2,
      3,
      4,
      11,
      19,
      21
    ],
    &quot;description&quot;: &quot;React hook library packaging and React spinner component maintenance&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      20,
      23,
      24,
      25
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      11
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      11,
      19,
      21,
      29,
      31
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      11
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      13,
      15,
      18,
      19,
      21
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      11
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;implicit&quot;
  }
}</pre>

## Bundle 20: `berniexie` — `2016-04-01`

Items in bundle: 7

### Bundle text

<pre>item_index: 1
created_at: 2016-04-20 18:39:38
event_type: PullRequestEvent
repo_name: cornsuite/imagepop-ui
title: Revert &quot;Show original by default&quot;
body:
This reverts commit d19a9a5ddcb06eca7c5bebe21ffaf8255e096ee8.

Fixes a bug</pre>

<pre>item_index: 2
created_at: 2016-04-20 05:53:59
event_type: PullRequestEvent
repo_name: cornsuite/imagepop-ui
title: Final PR
body:
Ready for Demo!</pre>

<pre>item_index: 3
created_at: 2016-04-13 03:28:59
event_type: PullRequestEvent
repo_name: berniexie/imagepop-ws
title: Spring security
body:
stateless authentication</pre>

<pre>item_index: 4
created_at: 2016-04-13 03:28:14
event_type: PullRequestEvent
repo_name: berniexie/imagepop-ws
title: Merge pull request #12 from berniexie/master
body:
FIrst PR to master!</pre>

<pre>item_index: 5
created_at: 2016-04-13 03:28:10
event_type: PullRequestEvent
repo_name: berniexie/imagepop-ws
title: Merge pull request #12 from berniexie/master
body:
FIrst PR to master!</pre>

<pre>item_index: 6
created_at: 2016-04-04 17:48:35
event_type: PullRequestEvent
repo_name: cornsuite/imagepop-ws
title: FIrst PR to master!
body:
Hey @vakopian there&#x27;s two separate things that are happening right now. Registering a user works, as well as uploading an image to the db. If you comment on certain sections of the code the corresponding person who worked on it will be able to change stuff up. Thanks!</pre>

<pre>item_index: 7
created_at: 2016-04-04 17:44:57
event_type: PullRequestEvent
repo_name: berniexie/imagepop-ws
title: Useraccounts routes
body:
- not sure if point 5 you mentioned last time is completed.
- I opened a PR first here so we can fix the changes and merge it into the fork&#x27;s master @vakopian </pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      6
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      6
    ],
    &quot;description&quot;: &quot;imagepop web application with UI and Spring-based web service, including user authentication, image upload, and demo preparation&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      6,
      7
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      6
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      6
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 21: `crisbodnar` — `2022-10-01`

Items in bundle: 5

### Bundle text

<pre>item_index: 1
created_at: 2022-12-24 12:32:37
event_type: PullRequestEvent
repo_name: crisbodnar/crisbodnar.github.io
title: Update design
body:
None</pre>

<pre>item_index: 2
created_at: 2022-12-24 12:32:24
event_type: PullRequestEvent
repo_name: crisbodnar/crisbodnar.github.io
title: Update design
body:
None</pre>

<pre>item_index: 3
created_at: 2022-10-17 13:33:45
event_type: PullRequestEvent
repo_name: bgavran/Category_Theory_Machine_Learning
title: Paper suggestion
body:
Suggesting our paper on Neural Sheaf Diffusion (accepted at NeurIPS 2022) </pre>

<pre>item_index: 4
created_at: 2022-10-16 18:44:34
event_type: IssueCommentEvent
repo_name: twitter-research/cwn
title: Format of TUDataset txt file
body:
As explained in the README, the TUDatasets should be downloaded from https://www.dropbox.com/s/2ekun30wxyxpcr7/datasets.zip?dl=0 

Let us now if you have further questions. </pre>

<pre>item_index: 5
created_at: 2022-10-16 18:44:34
event_type: IssuesEvent
repo_name: twitter-research/cwn
title: Format of TUDataset txt file
body:
Hi I&#x27;m currently working on running TUDatasets (REDDITBINRARY &amp; NCI109) by running following command
```
sh ./exp/scripts/cwn-nci109.sh
sh ./exp/scripts/mpsn-redditb.sh
```

I checked REDDITBINARY &amp; NCI109 from [here](https://chrsmrrs.github.io/datasets/docs/datasets/) but noticed that they have multiple types of txt file such as..
[ REDDITBINARY ]
* REDDIT-BINARY_A.txt
* REDDIT-BINARY_graph_indicator.txt
* REDDIT-BINARY_graph_labels.txt

[ NCI109_A ]
* NCI109_A.txt
* NCI109_graph_indicator.txt
* NCI109_graph_labels.txt
* NCI109_node_labels.txt

However I found that data/tu_utils.py -&gt;def load_data(path, dataset, degree_as_tag): only takes one txt file.
```
## data/tu_utils.py
def load_data(path, dataset, degree_as_tag):
    &quot;&quot;&quot;
        dataset: name of dataset
        test_proportion: ratio of test train split
        seed: random seed for random splitting of dataset
    &quot;&quot;&quot;

    print(&#x27;loading data&#x27;)
    g_list = []
    label_dict = {}
    feat_dict = {}

    with open(&#x27;%s/%s.txt&#x27; % (path, dataset), &#x27;r&#x27;) as f: ## &lt;- only takes one txt file..
        n_g = int(f.readline().strip())
        for i in range(n_g):
            row = f.readline().strip().split()
            n, l = [int(w) for w in row]
            if not l in label_dict:
                mapped = len(label_dict)
                label_dict[l] = mapped
            g = nx.Graph()
            node_tags = []
            node_features = []
            n_edges = 0
            f</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      5
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;research&quot;,
    &quot;citations&quot;: [
      3,
      4,
      5
    ],
    &quot;description&quot;: &quot;Research-domain engagement: suggesting a NeurIPS 2022 paper on Neural Sheaf Diffusion to a category-theory/ML repository and answering a user question about TUDataset format on the CWN repo.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      5
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      5
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 22: `cabello` — `2012-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2012-05-08 22:01:44
event_type: PullRequestEvent
repo_name: tokuhirom/go-examples
title: Update twitter client example to work on go 1.0.x
body:
Hey,

I was studying Go and I managed to run this example with &quot;some&quot; modifications, hehe

Great job with those examples,</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;Updating a Go Twitter client example for Go 1.0.x compatibility while learning the language.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 2
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 23: `changhiskhan` — `2019-07-01`

Items in bundle: 2

### Bundle text

<pre>item_index: 1
created_at: 2019-09-25 08:32:11
event_type: IssueCommentEvent
repo_name: combust/mleap
title: [xgboost][databricks][scala] key not found xgboost.regression
body:
Thanks @mengxr ! I will give this a shot asap.</pre>

<pre>item_index: 2
created_at: 2019-09-10 19:57:27
event_type: IssuesEvent
repo_name: combust/mleap
title: [xgboost][databricks][scala] key not found xgboost.regression
body:
Hi, I was wondering if this is a known issue or if I&#x27;m doing something obviously wrong.

I&#x27;m on a databricks runtime 5.4 ML cluster with a scala notebook. I&#x27;m essentially trying to reproduce one of the [mleap-xgboost-spark unit tests](https://github.com/combust/mleap/blob/master/mleap-xgboost-spark/src/test/scala/ml/dmlc/xgboost4j/scala/spark/mleap/XGBoostRegressionModelParitySpec.scala) but it fails on `loadMleapBundle`.

I&#x27;ve ensured that the cluster has mleap-runtime and mleap-xgboost-runtime jars attached. The remaining dependencies should already be part of the databricks runtime.

Are there any scala examples showing how to use the mleap-xgboost integration from within a databricks notebook?

Thanks!</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;other&quot;,
    &quot;citations&quot;: [
      2
    ],
    &quot;description&quot;: &quot;Reporting a bug and seeking help with mleap-xgboost integration on Databricks&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 2
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      2
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 24: `aaravbajaj012` — `2023-01-01`

Items in bundle: 19

### Bundle text

<pre>item_index: 1
created_at: 2023-02-18 21:25:09
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Admin
body:
None</pre>

<pre>item_index: 2
created_at: 2023-02-18 21:25:03
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Admin
body:
None</pre>

<pre>item_index: 3
created_at: 2023-02-18 21:10:34
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: prevent submissions
body:
Only at 4 pm</pre>

<pre>item_index: 4
created_at: 2023-02-18 20:15:44
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Tournament
body:
remove ability to see tournaments in match history.</pre>

<pre>item_index: 5
created_at: 2023-02-18 20:15:25
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: prevent submissions
body:
Only at 4 pm</pre>

<pre>item_index: 6
created_at: 2023-02-18 20:01:45
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Tournament
body:
remove ability to see tournaments in match history.</pre>

<pre>item_index: 7
created_at: 2023-02-18 19:59:30
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Profile
body:
None</pre>

<pre>item_index: 8
created_at: 2023-02-18 19:59:10
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Profile
body:
None</pre>

<pre>item_index: 9
created_at: 2023-02-18 00:33:04
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: added match history row shading
body:
None</pre>

<pre>item_index: 10
created_at: 2023-02-18 00:32:59
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: added match history row shading
body:
None</pre>

<pre>item_index: 11
created_at: 2023-02-17 18:20:21
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: profile pic avatars added
body:
None</pre>

<pre>item_index: 12
created_at: 2023-02-17 18:12:07
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Registration
body:
removed user registration route, updated registration api endpoint to store emails in database, updated login screen to not allow registration.</pre>

<pre>item_index: 13
created_at: 2023-02-17 15:39:18
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Registration
body:
removed user registration route, updated registration api endpoint to store emails in database, updated login screen to not allow registration.</pre>

<pre>item_index: 14
created_at: 2023-02-12 16:18:28
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: replay file links and match history formatting
body:
None</pre>

<pre>item_index: 15
created_at: 2023-02-12 16:03:49
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: replay file links and match history formatting
body:
None</pre>

<pre>item_index: 16
created_at: 2023-02-12 02:23:59
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Scrimmages
body:
rate limiter fixed</pre>

<pre>item_index: 17
created_at: 2023-02-12 02:23:51
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Scrimmages
body:
rate limiter fixed</pre>

<pre>item_index: 18
created_at: 2023-02-05 18:30:08
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Scrimmages
body:
Users can request unranked scrimmage and corresponding match history table is updated accordingly</pre>

<pre>item_index: 19
created_at: 2023-02-05 18:29:55
event_type: PullRequestEvent
repo_name: ACM-CMU/awap-dashboard
title: Scrimmages
body:
Users can request unranked scrimmage and corresponding match history table is updated accordingly</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;description&quot;: &quot;Competition dashboard for ACM-CMU AWAP event with admin controls, match history, scrimmage management, registration, and user profiles&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      3,
      4,
      12,
      16,
      18
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 25: `crisbodnar` — `2017-07-01`

Items in bundle: 6

### Bundle text

<pre>item_index: 1
created_at: 2017-08-21 11:58:45
event_type: IssueCommentEvent
repo_name: petergtz/pegomock
title: Type check for return values
body:
Awesome. I wrote a design doc inside Improbable (https://improbable.io/) to switch to this mock library because it has type checks and it&#x27;s much better than testify mocks. Atm this is the only downside of this library. If we decide to do this switch (in the next few days) I am more than happy to implement this change.</pre>

<pre>item_index: 2
created_at: 2017-08-21 08:53:26
event_type: IssueCommentEvent
repo_name: petergtz/pegomock
title: Type check for return values
body:
If you want to keep it in the exact style of Mockito I don&#x27;t see any nice solution. The best thing I can think of right now is 
`mock.On.smth(1).Return(1234)`
and in this way we avoid the use of global methods like When which complicate any way of doing type checks. It&#x27;s going to be only generated code.
I agree the When style is nice but we don&#x27;t have generics :( and this is a significant improvement for the library. You can keep both versions in order not to break existent stuff.

What do you think @petergtz ?</pre>

<pre>item_index: 3
created_at: 2017-08-19 23:17:17
event_type: PullRequestEvent
repo_name: gaearon/redux-thunk
title: Allow Dispatch of Redux actions as well
body:
None</pre>

<pre>item_index: 4
created_at: 2017-08-19 21:56:38
event_type: IssuesEvent
repo_name: petergtz/pegomock
title: Type check for return values
body:
It would be useful to have a typecheck on the return value at compile time. Right now if I have
`
func smth(a int) int {
//some code here
}
`
I can safely write this without generating any compile time error:
`
When(struct.smth(1)).ThenReturn(&quot;Not an int&quot;, &quot;One more invalid paramater&quot;)
`</pre>

<pre>item_index: 5
created_at: 2017-08-17 10:42:10
event_type: PullRequestEvent
repo_name: improbable-eng/grpc-web
title: Replace grpc.Code with Code
body:
None</pre>

<pre>item_index: 6
created_at: 2017-08-17 10:27:42
event_type: PullRequestEvent
repo_name: improbable-eng/grpc-web
title: Fix small error in README
body:
- if statement was missing ()
- grpc.Code does not exist. Code.OK should be used instead</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      4,
      5,
      6
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2,
      4,
      5,
      6
    ],
    &quot;description&quot;: &quot;Contributing to Go mock library pegomock with type-checking feature proposals, plus small PRs to grpc-web and redux-thunk.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      4,
      5,
      6
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      5,
      6
    ],
    &quot;value&quot;: 2
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      4
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 26: `aliscott` — `2017-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2017-12-27 13:09:25
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: Add notes about database backups.
body:
Should we make https://github.com/abarcloud/abar-database-backup an official template?</pre>

<pre>item_index: 2
created_at: 2017-12-22 11:04:10
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: [redis] Manual failover instructions for zero-downtime
body:
[View Redis docs](https://github.com/abarcloud/docs/blob/feature/redis-failover/additional-services/redis.md)</pre>

<pre>item_index: 3
created_at: 2017-12-22 11:03:39
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section
body:
[View Logs docs](https://github.com/abarcloud/docs/blob/feature/router-logs/management/logs.md)</pre>

<pre>item_index: 4
created_at: 2017-12-21 10:24:06
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: Add notes about database backups.
body:
Should we make https://github.com/abarcloud/abar-database-backup an official template?</pre>

<pre>item_index: 5
created_at: 2017-12-21 10:15:27
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
When would a user do this? If they get a connection error, should they run this command and retry?</pre>

<pre>item_index: 6
created_at: 2017-12-20 14:24:25
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Do we need this line?</pre>

<pre>item_index: 7
created_at: 2017-12-20 14:24:09
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
&gt; Run commands below for analyzing logs of your desired date and time
Run any of the commands below to analyze your logs.</pre>

<pre>item_index: 8
created_at: 2017-12-20 14:23:13
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Should we just always recommend 2Gi to make it easier for them?

&gt; Since this is a temporary pod it fine to give it high RAM.
Don&#x27;t think we need to say this</pre>

<pre>item_index: 9
created_at: 2017-12-20 14:22:18
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
fill -&gt; and fill out the form with the information provided</pre>

<pre>item_index: 10
created_at: 2017-12-20 14:21:10
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
to provide you with the required credentials</pre>

<pre>item_index: 11
created_at: 2017-12-20 14:20:50
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Don&#x27;t think we need to tell them all these details. Maybe something like
&gt; Some HTTP logs like 504s (Gateway timeouts) are not visible in your pods&#x27; logs, since they are caused by requests timing out before the pod responds. </pre>

<pre>item_index: 12
created_at: 2017-12-20 14:20:32
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Router logs -&gt; Load balancer logs</pre>

<pre>item_index: 13
created_at: 2017-12-20 14:17:43
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Should this be `###`?</pre>

<pre>item_index: 14
created_at: 2017-12-20 14:17:01
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: [logs] Add router logs section.
body:
Should we change &quot;primary Router&quot; to &quot;load balancers&quot;</pre>

<pre>item_index: 15
created_at: 2017-12-14 08:00:23
event_type: PullRequestReviewCommentEvent
repo_name: aramalipoor/abar-log
title: Initial Commit
body:
How does this handle SIGTERMs? You can do this gracefully using something like:

```go
c.Start()

// Handle SIGINT and SIGTERM.
ch := make(chan os.Signal)
signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
log.Info(&lt;-ch)

// Stop the service gracefully.
c.Stop()
log.Info(&quot;Done&quot;)
```</pre>

<pre>item_index: 16
created_at: 2017-12-14 07:57:42
event_type: PullRequestReviewCommentEvent
repo_name: aramalipoor/abar-log
title: Initial Commit
body:
We use https://github.com/urfave/cli in other projects</pre>

<pre>item_index: 17
created_at: 2017-12-07 12:39:27
event_type: IssuesEvent
repo_name: openshift/origin
title: GitHub oauth provider gets blank email
body:
When using the GitHub oauth provider to log in, the user&#x27;s email does not always get added to the identity&#x27;s extra meta data.

This is because the call to `https://api.github.com/user` can return null for the email if user has not selected a Public email in their public profile here https://github.com/settings/profile.

However, with the `user: email` scope, you can call `https://api.github.com/user/emails` to see all of the user&#x27;s email addresses and then filter by primary. Here is an example response:
```
[
  {
    &quot;email&quot;: &quot;email1@example.com&quot;,
    &quot;primary&quot;: false,
    &quot;verified&quot;: true,
    &quot;visibility&quot;: null
  },
  {
    &quot;email&quot;: &quot;email2@example.com&quot;,
    &quot;primary&quot;: true,
    &quot;verified&quot;: true,
    &quot;visibility&quot;: &quot;public&quot;
  }
]
```

##### Version
```
openshift version
openshift v3.6.0+c4dd4cf
kubernetes v1.6.1+5115d708d7
etcd 3.2.1
```

##### Steps To Reproduce
1. Use a GitHub user with no email selected for &quot;Public email&quot; under https://github.com/settings/profile.
2. Log in to your OpenShift dashboard using the GitHub IDP with that user.
3. Check the newly created identity:
  ```
  oc get identities GitHub.com:&lt;id&gt; -o yaml
  ```

##### Current Result

It does not show an email against the identity.

##### Expected Result

It shows the user&#x27;s primary email from GitHub.
</pre>

<pre>item_index: 18
created_at: 2017-12-04 14:10:23
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Varnish Cache in additional services docs section
body:
There&#x27;s no link here for `[this repository]`</pre>

<pre>item_index: 19
created_at: 2017-12-04 14:10:12
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Varnish Cache in additional services docs section
body:
We are using 4.1 but this link is for 4.0. Will this work ok?</pre>

<pre>item_index: 20
created_at: 2017-12-04 14:07:37
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Varnish Cache in additional services docs section
body:
The AbarCloud Varnish image includes sensible pre-defined configurations for many application use cases.</pre>

<pre>item_index: 21
created_at: 2017-12-04 14:06:11
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Varnish Cache in additional services docs section
body:
Should we tell them how to change the route?</pre>

<pre>item_index: 22
created_at: 2017-12-04 12:00:43
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-varnish
title: Initial commit for Varnish 4.1.9
body:
Do we want these in the entrypoint? So they are set if we `rsh` into the container?</pre>

<pre>item_index: 23
created_at: 2017-12-04 11:59:57
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-varnish
title: Initial commit for Varnish 4.1.9
body:
We use 3.6 for most things just now so best to keep it consistent</pre>

<pre>item_index: 24
created_at: 2017-12-04 11:57:50
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Varnish Cache in additional services docs section
body:
We can create a cache category, not sure where redis fits though... it&#x27;s a datastore that can be used as a cache</pre>

<pre>item_index: 25
created_at: 2017-12-04 11:55:47
event_type: PullRequestEvent
repo_name: abarcloud/abar-redis
title: Use redis-replicated as docker image name
body:
None</pre>

<pre>item_index: 26
created_at: 2017-12-04 10:48:56
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-varnish
title: Initial commit for Varnish 4.1.9
body:
Why 3.5, not 3.6?</pre>

<pre>item_index: 27
created_at: 2017-11-30 11:06:38
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Redis-replicated section
body:
cheap -&gt; inexpensive</pre>

<pre>item_index: 28
created_at: 2017-11-30 10:59:35
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Redis-replicated section
body:
To be able to connect to a Sentinel-based Redis setup your client needs to understand how to talk to sentinel.

maybe:

To connect to a Master/Slave replicated Redis, you will need to use a client that supports Sentinel.</pre>

<pre>item_index: 29
created_at: 2017-11-30 10:57:42
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Redis-replicated section
body:
Master/Slave replication -&gt; Master/Slave replicated Redis service</pre>

<pre>item_index: 30
created_at: 2017-11-30 10:56:41
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Redis-replicated section
body:
need -&gt; needs</pre>

<pre>item_index: 31
created_at: 2017-11-30 10:56:20
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/docs
title: Add Redis-replicated section
body:
`that a [cron job]` -&gt; and a [cron job]`. Also that link has no `)`</pre>

<pre>item_index: 32
created_at: 2017-11-29 17:24:19
event_type: PullRequestEvent
repo_name: abarcloud/abar-redis
title: Use supervisor to run Redis and Sentinel services
body:
* Used Alpine 
* Run Sentinel+Redis using supervisor
* Detect Redis role from k8s&#x27; Sentinel headless service
* Cover some failover edge-cases e.g. If Pod&#x27;s container fails/restarts.</pre>

<pre>item_index: 33
created_at: 2017-11-28 14:23:53
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-redis
title: Use supervisor to run Redis and Sentinel services
body:
Yeah that looks right - so I think this will be OK.</pre>

<pre>item_index: 34
created_at: 2017-11-28 10:35:21
event_type: IssueCommentEvent
repo_name: abarcloud/abar-redis
title: Use supervisor to run Redis and Sentinel services
body:
LGTM :+1:</pre>

<pre>item_index: 35
created_at: 2017-11-27 16:11:15
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-redis
title: Use supervisor to run Redis and Sentinel services
body:
Guess this still needs to be updated. Should we just set the default to 0 so it&#x27;s unlimited and we don&#x27;t know the max memory of the pod. Guessing this will always be set anyway in the env.</pre>

<pre>item_index: 36
created_at: 2017-11-27 16:06:29
event_type: PullRequestReviewCommentEvent
repo_name: abarcloud/abar-redis
title: Use supervisor to run Redis and Sentinel services
body:
Do we know what the size difference between redis and redis-alpine is and if it&#x27;s worth using redis-alpine? It&#x27;s not something we&#x27;ve really looked at before for our hosted services, but we&#x27;re using alpine now for all our example dockerfiles. Maybe @alikhajeh1 has opinions on if we should start using alpine for our services.</pre>

<pre>item_index: 37
created_at: 2017-11-23 14:48:45
event_type: IssueCommentEvent
repo_name: abarcloud/docs
title: Add docs for deploying existing Docker images
body:
lgtm</pre>

<pre>item_index: 38
created_at: 2017-11-23 10:15:40
event_type: PullRequestEvent
repo_name: abarcloud/custom-autoscaler
title: Add redis support
body:
Thanks to @amirhabibzadeh for this.</pre>

<pre>item_index: 39
created_at: 2017-11-20 10:46:19
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: Resize and compress images.
body:
None</pre>

<pre>item_index: 40
created_at: 2017-11-15 15:30:56
event_type: PullRequestEvent
repo_name: abarcloud/docs
title: Db notes
body:
Not sure why the PG creation isn&#x27;t working as expected, the user is able to connect to other databases.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      5,
      8,
      11,
      20,
      21
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;infrastructure&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      15,
      22,
      25,
      32,
      38,
      40
    ],
    &quot;description&quot;: &quot;Building AbarCloud platform infrastructure components including Redis replicated service, Varnish cache image, database backup templates, router/load balancer logging, and custom autoscaler with Redis support.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      5,
      6,
      7,
      8,
      15,
      16,
      34,
      38
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      20,
      27
    ],
    &quot;value&quot;: 2
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      15,
      22,
      25,
      32,
      38,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      20,
      23,
      32,
      38
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      15,
      22,
      25,
      32,
      38,
      40
    ],
    &quot;value&quot;: 3
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 27: `dahyman91` — `2021-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2021-12-10 17:48:18
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: titleize me, captain
body:
None</pre>

<pre>item_index: 2
created_at: 2021-12-10 17:48:01
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: titleize me, captain
body:
None</pre>

<pre>item_index: 3
created_at: 2021-12-10 15:13:49
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: new category functionality
body:
None</pre>

<pre>item_index: 4
created_at: 2021-12-10 15:10:52
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: new category functionality
body:
None</pre>

<pre>item_index: 5
created_at: 2021-12-10 15:10:37
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: dans latest work
body:
None</pre>

<pre>item_index: 6
created_at: 2021-12-10 15:10:31
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: dans latest work
body:
None</pre>

<pre>item_index: 7
created_at: 2021-12-10 15:09:28
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: added comment posting/comment deleting routes and functionality
body:
None</pre>

<pre>item_index: 8
created_at: 2021-12-10 15:09:22
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: added comment posting/comment deleting routes and functionality
body:
None</pre>

<pre>item_index: 9
created_at: 2021-12-10 15:08:56
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Maxtown
body:
None</pre>

<pre>item_index: 10
created_at: 2021-12-09 22:06:00
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: Deploy
body:
None</pre>

<pre>item_index: 11
created_at: 2021-12-09 22:05:54
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: Deploy
body:
None</pre>

<pre>item_index: 12
created_at: 2021-12-09 22:03:49
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Deploy
body:
None</pre>

<pre>item_index: 13
created_at: 2021-12-09 19:44:40
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: comment functionality and styling
body:
None</pre>

<pre>item_index: 14
created_at: 2021-12-09 16:51:20
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added new_comment functionality
body:
None</pre>

<pre>item_index: 15
created_at: 2021-12-09 16:51:14
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added new_comment functionality
body:
None</pre>

<pre>item_index: 16
created_at: 2021-12-09 16:50:30
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added new_comment functionality
body:
None</pre>

<pre>item_index: 17
created_at: 2021-12-09 16:41:00
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added new_comment functionality
body:
None</pre>

<pre>item_index: 18
created_at: 2021-12-09 16:40:25
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: Dans new branch
body:
None</pre>

<pre>item_index: 19
created_at: 2021-12-09 16:40:20
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: Dans new branch
body:
None</pre>

<pre>item_index: 20
created_at: 2021-12-09 16:39:17
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: more stuff
body:
None</pre>

<pre>item_index: 21
created_at: 2021-12-09 16:38:22
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: more stuff
body:
None</pre>

<pre>item_index: 22
created_at: 2021-12-09 16:38:09
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: added new_comment routes
body:
None</pre>

<pre>item_index: 23
created_at: 2021-12-09 16:37:34
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: added new_comment routes
body:
None</pre>

<pre>item_index: 24
created_at: 2021-12-08 21:45:50
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added input fields
body:
None</pre>

<pre>item_index: 25
created_at: 2021-12-08 21:45:45
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added input fields
body:
None</pre>

<pre>item_index: 26
created_at: 2021-12-08 21:05:18
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: all core deliverables included
body:
None</pre>

<pre>item_index: 27
created_at: 2021-12-08 21:05:12
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: all core deliverables included
body:
None</pre>

<pre>item_index: 28
created_at: 2021-12-08 15:44:14
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: Dans branch
body:
None</pre>

<pre>item_index: 29
created_at: 2021-12-08 15:44:04
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project
title: Dans branch
body:
None</pre>

<pre>item_index: 30
created_at: 2021-12-08 15:36:46
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Dans branch
body:
None</pre>

<pre>item_index: 31
created_at: 2021-12-07 11:40:06
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added semantic and menu
body:
None</pre>

<pre>item_index: 32
created_at: 2021-12-06 23:23:30
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Dans branch
body:
None</pre>

<pre>item_index: 33
created_at: 2021-12-06 23:22:18
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Dans branch
body:
None</pre>

<pre>item_index: 34
created_at: 2021-12-06 23:21:51
event_type: PullRequestEvent
repo_name: learn-co-curriculum/phase-3-sinatra-react-project
title: Dans branch
body:
None</pre>

<pre>item_index: 35
created_at: 2021-12-06 18:10:25
event_type: PullRequestEvent
repo_name: dahyman91/message-board-project-frontend
title: added semantic and menu
body:
None</pre>

<pre>item_index: 36
created_at: 2021-11-19 18:27:03
event_type: PullRequestEvent
repo_name: dahyman91/financial-dashboard
title: Added datalabels
body:
None</pre>

<pre>item_index: 37
created_at: 2021-11-19 18:25:47
event_type: PullRequestEvent
repo_name: dahyman91/financial-dashboard
title: Added datalabels
body:
None</pre>

<pre>item_index: 38
created_at: 2021-11-19 18:25:27
event_type: PullRequestEvent
repo_name: dahyman91/financial-dashboard
title: table updated
body:
None</pre>

<pre>item_index: 39
created_at: 2021-11-19 18:25:15
event_type: PullRequestEvent
repo_name: dahyman91/financial-dashboard
title: table updated
body:
None</pre>

<pre>item_index: 40
created_at: 2021-11-18 22:20:58
event_type: PullRequestEvent
repo_name: dahyman91/financial-dashboard
title: finished
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      20,
      26
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      3,
      7,
      13,
      36
    ],
    &quot;description&quot;: &quot;A message-board application with separate backend (Sinatra) and frontend (React) repos, plus a financial-dashboard project; both appear to be curriculum or personal learning projects&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      5,
      18,
      28
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      20,
      26
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      3,
      36
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      9,
      26,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      20,
      26
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      9,
      26
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 28: `daanishkhazi` — `2018-04-01`

Items in bundle: 16

### Bundle text

<pre>item_index: 1
created_at: 2018-05-29 00:02:33
event_type: PullRequestEvent
repo_name: eecs394-s18/pursist
title: Form validator
body:
None</pre>

<pre>item_index: 2
created_at: 2018-05-29 00:02:25
event_type: PullRequestEvent
repo_name: eecs394-s18/pursist
title: Form validator
body:
None</pre>

<pre>item_index: 3
created_at: 2018-05-21 04:52:40
event_type: PullRequestEvent
repo_name: eecs394-s18/pursist
title: Added delete card button
body:
None</pre>

<pre>item_index: 4
created_at: 2018-05-21 02:26:24
event_type: PullRequestEvent
repo_name: eecs394-s18/pursist
title: front page styling/cards
body:
None</pre>

<pre>item_index: 5
created_at: 2018-05-20 19:51:47
event_type: IssueCommentEvent
repo_name: eecs394-s18/pursist
title: front page styling/cards
body:
can someone check if this works on their computer, my postgres env is kinda weird, so you might need to change make your .env back to how it was before, but im not sure why it commited since its in gitignore but yea</pre>

<pre>item_index: 6
created_at: 2018-05-20 19:48:59
event_type: PullRequestEvent
repo_name: eecs394-s18/pursist
title: front page styling/cards
body:
None</pre>

<pre>item_index: 7
created_at: 2018-04-28 02:42:38
event_type: IssuesEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: Add edit feature on professor side for class name and lecture names if possible
body:
None</pre>

<pre>item_index: 8
created_at: 2018-04-28 02:42:25
event_type: PullRequestEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: prof pages edit feature
body:
None</pre>

<pre>item_index: 9
created_at: 2018-04-27 21:55:42
event_type: PullRequestEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: prof pages edit feature
body:
None</pre>

<pre>item_index: 10
created_at: 2018-04-27 21:51:06
event_type: IssuesEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: radio -&gt; button on all pages
body:
None</pre>

<pre>item_index: 11
created_at: 2018-04-27 20:27:07
event_type: IssuesEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: radio -&gt; button on all pages
body:
None</pre>

<pre>item_index: 12
created_at: 2018-04-23 19:50:23
event_type: PullRequestEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: home button -&gt; class pages
body:
fixes home reset issue</pre>

<pre>item_index: 13
created_at: 2018-04-23 19:35:13
event_type: IssueCommentEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: Reset home page
body:
pull request made</pre>

<pre>item_index: 14
created_at: 2018-04-23 19:35:04
event_type: IssuesEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: Reset home page
body:
Home page will direct to class list</pre>

<pre>item_index: 15
created_at: 2018-04-23 19:34:50
event_type: IssuesEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: Reset home page
body:
Home page will direct to class list</pre>

<pre>item_index: 16
created_at: 2018-04-23 19:34:21
event_type: PullRequestEvent
repo_name: eecs394-s18/ClassConfusion-Refactor
title: home button -&gt; class pages
body:
fixes home reset issue</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      5,
      13
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      3,
      4,
      8,
      12
    ],
    &quot;description&quot;: &quot;Web application features including form validators, card UI styling, delete buttons, and edit features for class-related apps in a university course context.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      5,
      8,
      12,
      13
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      8,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      8,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      8,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      8,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      8,
      12
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 29: `danielhanchen` — `2022-07-01`

Items in bundle: 6

### Bundle text

<pre>item_index: 1
created_at: 2022-07-14 08:27:28
event_type: IssueCommentEvent
repo_name: danielhanchen/hyperlearn
title: Installation Problem
body:
Heyy! Ohhh oops! So we&#x27;re still in the process of fixing things up - I think I might have accidentally not pushed a newer update.

So currently the package is un-usable as of now - you can join our Discord (link on frontpage) for more updates.

It&#x27;s been real hectic, so I&#x27;ll be sure to tell you when it&#x27;s all polished!</pre>

<pre>item_index: 2
created_at: 2022-07-08 18:01:47
event_type: IssueCommentEvent
repo_name: microsoft/recommenders
title: [FEATURE] Add CPU power check function for time performance tests
body:
PS I calculated by hand the Intel(R) Xeon(R) CPU E5-2673 v3 16 core GFLOPS Haswell AVX2:

16 cores * 2.4 GHz * 2 * 256 / 8 / 8 = 307.2 GFLOPs or so.

It seems like a Turbo Boost of 3.2 GHz is possible, though I guess that&#x27;s for like SOME cores out of 16.
At max maybe (2.4 + 3.2)/2 = 2.8GHz so

16 cores * 2.8 GHz * 2 * 256 / 8 / 8 = 358.4 GFLOPs or so.</pre>

<pre>item_index: 3
created_at: 2022-07-08 17:52:09
event_type: IssueCommentEvent
repo_name: microsoft/recommenders
title: [FEATURE] Add CPU power check function for time performance tests
body:
My bad, Google Colab was using an old psutil version</pre>

<pre>item_index: 4
created_at: 2022-07-08 17:47:18
event_type: IssueCommentEvent
repo_name: microsoft/recommenders
title: [FEATURE] Add CPU power check function for time performance tests
body:
PS I found `psutil` to not function on Google Colab, but `cpuinfo` works - very weird - I&#x27;ll probably report this issue to `psutil`</pre>

<pre>item_index: 5
created_at: 2022-07-08 17:43:32
event_type: IssueCommentEvent
repo_name: microsoft/recommenders
title: [FEATURE] Add CPU power check function for time performance tests
body:
```
import cpuinfo

def get_gflops():
    &quot;&quot;&quot;
    Uses https://github.com/workhorsy/py-cpuinfo to get CPU info.
    We make some assumptions on the FLOPs for each CPU.
    We assume from https://uops.info/table.html:
    1. AVX512 can dispatch 2 FMAs (8 doubles) in 1 cycle
    2. AVX2 can dispatch 2 FMAs (4 doubles) in 1 cycle
    3. AVX / FMA4 can dispatch only 1 FMA (4 doubles) in 1 cycle
    4. SSE (2 doubles) can dispatch only 1 multiply followed by an add in 1 cycle

    Then GFLOPS = # cores * cpu frequency in GHz * # dispatch * # FMAs in 1 cycle
    &quot;&quot;&quot;
    try:
        cpu_info = cpuinfo.get_cpu_info()
        cpu_info_flags = frozenset(cpu_info[&quot;flags&quot;])

        # In GigaHertz
        cpu_frequency = cpu_info[&quot;hz_advertised&quot;][0] / 1000 / 1000 / 1000
        cpu_cores = cpu_info[&quot;count&quot;]

        # https://numpy.org/devdocs/reference/simd/build-options.html
        if &quot;avx512&quot; in cpu_info_flags:
            dispatch_per_cycle = 2
            vector_width_bits  = 512
        elif &quot;avx2&quot; in cpu_info_flags:
            dispatch_per_cycle = 2
            vector_width_bits  = 256
        elif &quot;avx&quot; in cpu_info_flags or &quot;fma4&quot;:
            dispatch_per_cycle = 1
            vector_width_bits  = 256
        elif &quot;sse&quot; in cpu_info_flags:
            dispatch_per_cycle = 1
            vector_width_bits  = 128
        else:
            # Not sure on ARM cpus
            dispatch_per_cycle = 2
            vector_width = 256
        pass
</pre>

<pre>item_index: 6
created_at: 2022-07-06 16:52:56
event_type: PullRequestEvent
repo_name: danielhanchen/hyperlearn
title: Making discord link never expire
body:
https://discord.gg/k8AtkZqNwr</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      6
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      5,
      6
    ],
    &quot;description&quot;: &quot;Maintaining hyperlearn (a machine learning library) and contributing CPU benchmarking code to microsoft/recommenders&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      6
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      2,
      3,
      4,
      5
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      6
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      6
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 30: `cmflannery` — `2018-07-01`

Items in bundle: 12

### Bundle text

<pre>item_index: 1
created_at: 2018-08-17 03:11:18
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Add a description of why the error was raised.

```python
raise ValueError(&#x27;What happened&#x27;)
```</pre>

<pre>item_index: 2
created_at: 2018-08-17 03:09:31
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Make a function for unit conversions.</pre>

<pre>item_index: 3
created_at: 2018-08-17 03:08:52
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Be careful doing this. In python2, this would be treated as integer division if 64 is not a float. Simple solution is to add `from __future__ import division` at the top.</pre>

<pre>item_index: 4
created_at: 2018-08-17 03:07:09
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
We will be using google style docstrings:
http://www.sphinx-doc.org/en/stable/ext/example_google.html</pre>

<pre>item_index: 5
created_at: 2018-08-17 03:05:54
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
These don&#x27;t need to be class definitions. Do this instead
```python
class fluid():
    &quot;&quot;&quot;Base fluid class&quot;&quot;&quot;
    def __init__(self, density, kv, sg):
        self.density = density
        self.kv = kv
        self.sg
```</pre>

<pre>item_index: 6
created_at: 2018-08-17 03:03:27
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
If this module is going to be useful for more than just Marginal Stability, we should put it in it&#x27;s own repository and make it it&#x27;s own package.</pre>

<pre>item_index: 7
created_at: 2018-08-17 03:02:48
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Docstring and shebang</pre>

<pre>item_index: 8
created_at: 2018-08-17 03:02:38
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Docstring stating what the inputs and outputs are.</pre>

<pre>item_index: 9
created_at: 2018-08-17 03:02:20
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
All of these individual statements should be wrapped in a function. Perhaps use a config file input like openrocketengine?</pre>

<pre>item_index: 10
created_at: 2018-08-17 03:01:50
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
Add a blank line at the end of the file.</pre>

<pre>item_index: 11
created_at: 2018-08-17 03:01:04
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
As mentioned on Instructions.txt, don&#x27;t copy the source for openrocketengine.</pre>

<pre>item_index: 12
created_at: 2018-08-17 03:00:32
event_type: PullRequestReviewCommentEvent
repo_name: rocketproplab/marginal-stability
title: Neal&#x27;s Not good enough to push to master branch
body:
You shouldn&#x27;t just copy the whole library. Use the library in your custom scripts. I.e.
`import openrocketengine as ore` at the top of the file.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      4,
      7,
      8
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      5,
      6,
      9,
      12
    ],
    &quot;description&quot;: &quot;Rocket propulsion engineering software library (marginal-stability) with code review feedback on structure, packaging, and proper library usage&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      6,
      9,
      11,
      12
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      6
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      5,
      6,
      12
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      6
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      5,
      6,
      9,
      11,
      12
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 31: `bluisana` — `2023-01-01`

Items in bundle: 9

### Bundle text

<pre>item_index: 1
created_at: 2023-03-30 13:15:22
event_type: PullRequestReviewCommentEvent
repo_name: transmute-industries/jsonld-to-cypher
title: Minor Changes to output merge statements
body:
irrelevant file has been removed. </pre>

<pre>item_index: 2
created_at: 2023-03-29 19:48:58
event_type: IssueCommentEvent
repo_name: rjsf-team/react-jsonschema-form
title: Optional object with required fields in react-jsonschema-form
body:
6 years later and it looks like this bug still exists.  I have a large amount of complex schemas that can&#x27;t be modified using &quot;depencies&quot; or other conditionals.  It is expected behavior of a schema that objects properties are not required if the object itself isn&#x27;t required.  I am testing this with the following simply schema. Is there any fix for this that I am missing that doesn&#x27;t involve changing the actual schemas? 

`schema: {
            type: &#x27;object&#x27;,
            properties: {
              person: {
                type: &#x27;object&#x27;,
                properties: {
                  id: {
                    type: &#x27;string&#x27;,
                  },
                  name: {
                    type: &#x27;string&#x27;,
                  },
                },
                required: [&#x27;name&#x27;],
              },
            },
            example: &#x27;{}&#x27;,
          }`</pre>

<pre>item_index: 3
created_at: 2023-03-22 17:45:36
event_type: PullRequestEvent
repo_name: transmute-industries/jsonld-to-cypher
title: Minor Changes to output merge statements
body:
expanded the blanknode identification by passing the entire nodelabel to the blanknode method. 

changed the nodetonodelabel method to output multiple labels as an array rather than a colon separated string. 
</pre>

<pre>item_index: 4
created_at: 2023-01-28 17:07:16
event_type: PullRequestEvent
repo_name: nvm-sh/nvm
title: Update README.md
body:
I ran into an issue installing NVM on my Mac Book Pro.  I appended the nvm install instructions with the command to fix the scenario I ran into.</pre>

<pre>item_index: 5
created_at: 2023-01-19 14:13:23
event_type: IssueCommentEvent
repo_name: Ysurac/openmptcprouter
title: Raspberry PI Compute 4 I/O board and CM4
body:
Hey Ysurac, 

I still get the start4.elf: is not compatible.  This board requires newer software message with the v0.59.2alpha-5.4-r0+16819-1b6e9b3f64-bcm27xx-bcm2711-rpi-4-ext4-factory.img.  I will just keep checking back here periodically to look at the snapshot images.  If you remember, shoot me a message on here when you get the rpi4/bcm27xx images for 6.1 uploaded and I will give it a shot.  

Thanks</pre>

<pre>item_index: 6
created_at: 2023-01-15 23:06:36
event_type: IssueCommentEvent
repo_name: Ysurac/openmptcprouter
title: Raspberry PI Compute 4 I/O board and CM4
body:
Hey Ysurac, 

Is it possible for me to try to build an image of openmptcprouter for the version of openwrt that works on my device?  

If so could you give me a basic run down of how to accomplish this? 

Thanks, </pre>

<pre>item_index: 7
created_at: 2023-01-13 01:00:26
event_type: IssueCommentEvent
repo_name: Ysurac/openmptcprouter
title: Raspberry PI Compute 4 I/O board and CM4
body:
Hey Ysurac, 

I don&#x27;t know if this information would help you or not if you wanted to support this board but the latest image of openwrt worked fine for me. 

https://downloads.openwrt.org/releases/22.03.3/targets/bcm27xx/bcm2711/openwrt-22.03.3-bcm27xx-bcm2711-rpi-4-squashfs-factory.img.gz</pre>

<pre>item_index: 8
created_at: 2023-01-12 21:03:59
event_type: IssueCommentEvent
repo_name: Ysurac/openmptcprouter
title: Raspberry PI Compute 4 I/O board and CM4
body:
Thanks Ysurac,

</pre>

<pre>item_index: 9
created_at: 2023-01-12 17:31:47
event_type: IssuesEvent
repo_name: Ysurac/openmptcprouter
title: Raspberry PI Compute 4 I/O board and CM4
body:
Hello, 

I was pumped to tryout openmptcprouter on my new raspberrypi setup.  Unfortunately none of the images for CM4 will boot on my board :(.  Are there any images that use a newer PI firmware version hidden somewhere?  

![PXL_20230112_173006528](https://user-images.githubusercontent.com/1056677/212137891-3a5c9489-3cde-4f92-820f-fc6945f56702.jpg)
</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      3,
      4,
      5,
      6,
      9
    ],
    &quot;description&quot;: &quot;Contributing small fixes and feature changes to open-source developer tools including jsonld-to-cypher, nvm, and openmptcprouter, plus reporting bugs in react-jsonschema-form.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      2,
      5,
      6,
      7,
      9
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      4,
      2,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 32: `benadida` — `2011-10-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2011-12-30 21:01:21
event_type: IssuesEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
right now cookie-sessions have integrity protection, not confidentiality. We should encrypt them.</pre>

<pre>item_index: 2
created_at: 2011-12-30 20:34:03
event_type: IssuesEvent
repo_name: mozilla/browserid
title: if session expires in the middle of user using it, problems
body:
I haven&#x27;t seen this yet, but I&#x27;m guessing that, with the existing session approach and even our new one, we get into trouble if the session expires while the user is using BrowserID. This is probably rare, but can happen because we have a hard expiration time based on when the user loggedin.</pre>

<pre>item_index: 3
created_at: 2011-12-30 19:19:01
event_type: PullRequestEvent
repo_name: benadida/cookie-session
title: see code.
body:
None</pre>

<pre>item_index: 4
created_at: 2011-12-30 14:38:26
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: limit the size of POST body
body:
I would love some defense in the app code, too, before (or using a modified) bodyParser. Go for it and take it.</pre>

<pre>item_index: 5
created_at: 2011-12-30 14:35:57
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: IE8: Trying to sign into http://carrera.databits.net:9999 gets an error
body:
@shane-tomlinson quirksmode is awesome! I think we probably need to add the JSON2 library, sadly.</pre>

<pre>item_index: 6
created_at: 2011-12-30 01:23:11
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
only missing feature right now is management of the duration, will work on that asap, so I&#x27;m going to reopen this issue actually.</pre>

<pre>item_index: 7
created_at: 2011-12-30 01:23:08
event_type: IssuesEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
right now cookie-sessions have integrity protection, not confidentiality. We should encrypt them.</pre>

<pre>item_index: 8
created_at: 2011-12-30 01:21:59
event_type: IssuesEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
right now cookie-sessions have integrity protection, not confidentiality. We should encrypt them.</pre>

<pre>item_index: 9
created_at: 2011-12-29 23:56:05
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Back-end unit tests failing on local install
body:
yes, known heisenbug, ignore for now :)</pre>

<pre>item_index: 10
created_at: 2011-12-29 22:12:09
event_type: IssuesEvent
repo_name: mozilla/browserid
title: Cannot log in to BrowserId using stock browser on Froyo
body:
Android Build: 2.2.2
Browser: Stock
Website: http://www.mozillians.org

Steps to Reproduce:
1. Go to the website mentioned above.
2. Click on &quot;Log In&quot;

Actual Results:
New window is opened at connection error page at browserid.org

Expected Results:
New window is opened at browserid hosted sign on page</pre>

<pre>item_index: 11
created_at: 2011-12-29 22:12:07
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Cannot log in to BrowserId using stock browser on Froyo
body:
this is a dupe of #708 so I will close this one. Note that we may have fixed this in 2.2, but I&#x27;m not so sure yet.</pre>

<pre>item_index: 12
created_at: 2011-12-29 22:10:30
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Cannot log in to BrowserId using stock browser on Froyo
body:
@sammybahamas cool, that&#x27;s reassuring. We&#x27;re working on the assumption that most users have a default browser setup. That said, this is no longer an issue in android 2.3+. If we can find a workaround for 2.2, we&#x27;ll definitely let you know.</pre>

<pre>item_index: 13
created_at: 2011-12-29 22:04:28
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Cannot log in to BrowserId using stock browser on Froyo
body:
@sammybahamas any chance your phone is set up to not have a default browser? There is an Android 2.2 bug related to not having a default browser set.</pre>

<pre>item_index: 14
created_at: 2011-12-29 20:30:47
event_type: IssuesEvent
repo_name: mozilla/browserid
title: limit the size of POST body
body:
Defend against this attack:

http://www.cs.rice.edu/~scrosby/hash/CrosbyWallach_UsenixSec2003.pdf</pre>

<pre>item_index: 15
created_at: 2011-12-29 18:45:30
event_type: PullRequestEvent
repo_name: mozilla/django-browserid
title: authenticated users need browserid_form to change their email
body:
None</pre>

<pre>item_index: 16
created_at: 2011-12-29 18:16:08
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: BrowserID hangs on &quot;Communicating with server&quot; on iPad (iOS5)
body:
unable to reproduce, we suspect this is related to caching, see issue #226, please reopen if this happens again!</pre>

<pre>item_index: 17
created_at: 2011-12-29 18:16:08
event_type: IssuesEvent
repo_name: mozilla/browserid
title: BrowserID hangs on &quot;Communicating with server&quot; on iPad (iOS5)
body:
On an iPad the BrowserID popup hangs on &quot;Communicating with server&quot;.

Version: 5.0.1 (9A405)
Model: MB294LL

Reproduce:

1. Go to http://current.openphoto.me
1. Click sign in
1. Witness hanging on &quot;Communicating with server&quot;

Expected:

1. Go to http://current.openphoto.me
1. Click sign in
1. See sign in form</pre>

<pre>item_index: 18
created_at: 2011-12-29 18:12:27
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Cosmetics in bin/verifier
body:
sorry, we didn&#x27;t get to this in time before we updated the code, I&#x27;m closing this pull request but feel free to resubmit based on latest code.</pre>

<pre>item_index: 19
created_at: 2011-12-29 18:12:27
event_type: PullRequestEvent
repo_name: mozilla/browserid
title: Cosmetics in bin/verifier
body:
None</pre>

<pre>item_index: 20
created_at: 2011-12-29 18:09:05
event_type: IssuesEvent
repo_name: mozilla/browserid
title: BrowserID: Security hole when adding an email to an existing account.
body:
See security Bug 708875 - BrowserID: Security hole when adding an email to an existing account.

Adding a GitHub issue, so we do not forget about this bug.</pre>

<pre>item_index: 21
created_at: 2011-12-29 18:08:43
event_type: IssuesEvent
repo_name: mozilla/browserid
title: BrowserID: Security hole when adding an email to an existing account.
body:
See security Bug 708875 - BrowserID: Security hole when adding an email to an existing account.

Adding a GitHub issue, so we do not forget about this bug.</pre>

<pre>item_index: 22
created_at: 2011-12-29 17:43:58
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: It is possible to &quot;combine&quot; accounts through myfavoriteshow.org
body:
to @jbonacci: consolidate this bug with other similar account combination bugs into one tracking issue.</pre>

<pre>item_index: 23
created_at: 2011-12-29 17:37:24
event_type: IssuesEvent
repo_name: mozilla/browserid
title: Make a live link of MPL on the TOS page
body:
On the current TOS page for Diresworb.org, we can see the following:

Proprietary Rights

Mozilla does not grant you any intellectual property rights in the Services that are not specifically stated in this TOS. For example, this TOS does not provide the right to use any of Mozilla’s copyrights, trade names, trademarks, service marks, logos, domain names, or other distinctive brand features.

The Firefox Clients are distributed under and subject to the current version of the Mozilla Public License, located at http://www.mozilla.org/MPL. 


Please convert that to a live link (assuming it is a static link).


</pre>

<pre>item_index: 24
created_at: 2011-12-29 17:37:23
event_type: PullRequestEvent
repo_name: mozilla/browserid
title: Turn license URL in ToS into a clickable link (closes #382)
body:
None</pre>

<pre>item_index: 25
created_at: 2011-12-29 05:29:35
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: package.json is missing a few dependencies
body:
@fmarier ahah, you&#x27;re running on the bleeding edge :) Will close this for now, feel free to reopen if you notice this on a released version of node!</pre>

<pre>item_index: 26
created_at: 2011-12-29 05:29:35
event_type: IssuesEvent
repo_name: mozilla/browserid
title: package.json is missing a few dependencies
body:
After running &quot;npm install&quot; to install the browserid dependencies, I had to install these:

  npm install pkginfo
  npm install colors
  npm install stack-trace
  npm install async
  npm install qs
  npm install mime
  npm install mersenne

before I could successfully run it with &quot;npm start&quot;.</pre>

<pre>item_index: 27
created_at: 2011-12-29 05:16:51
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: package.json is missing a few dependencies
body:
which version of node are you running?</pre>

<pre>item_index: 28
created_at: 2011-12-28 22:27:06
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: Feature randomseed from server
body:
@lloyd I don&#x27;t know the exact implementation of node&#x27;s getRandom, we should test it.</pre>

<pre>item_index: 29
created_at: 2011-12-28 06:43:01
event_type: PullRequestEvent
repo_name: mozilla/browserid
title: moved to new assertion format, added a bunch of tests to check both old ...
body:
...and new formats, fixes #507</pre>

<pre>item_index: 30
created_at: 2011-12-28 06:42:07
event_type: IssuesEvent
repo_name: mozilla/browserid
title: Assertion uses base64-encoding twice
body:
I can&#x27;t work out the exact format of the &quot;assertion&quot; parameter, but it looks like it&#x27;s a base64 encoding of a JSON object which itself contains base64 data (or a dotted contatenation of the same). This is really inefficient - each time you base64-encode, you waste 2 bits per octet. You have to do it once for ASCII-armouring, but twice is surely unnecessary?

Gerv</pre>

<pre>item_index: 31
created_at: 2011-12-28 03:28:02
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
crud, I was under the impression that JSON serialize had an option for sorting keys. OK, I&#x27;ll see if I can find existing mutation detection. Some hints of it here:

http://stackoverflow.com/questions/1759987/detect-variable-change-in-javascript

but of course we need to watch for property changes where we don&#x27;t know the properties ahead of time. I&#x27;m sure there&#x27;s some existing proxy code for this. I&#x27;ll hold off on the temptation to cc /be</pre>

<pre>item_index: 32
created_at: 2011-12-28 02:33:35
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
gotcha, right, because if it&#x27;s just expiration time on the cookie, then resetting the cookie will extend the expiration time, which is not what we want.

I&#x27;m thinking proxies might be overkill, maybe JSON serialize and compare?</pre>

<pre>item_index: 33
created_at: 2011-12-28 02:27:32
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: encrypt cookie content
body:
one correction:

* we have to sign the cookie, not just encrypt it. Otherwise this might allow someone to rejigger the ciphertext around and mess things up. In general, not good to encrypt without signing, it&#x27;s typically asking for trouble. So we&#x27;ll do both.

and one question:

* what do you mean by &quot;self manages fixed durations?&quot; Do you mean that it auto-updates the cookie expiration to expose effectively 2-week (parameterizable) sessions?</pre>

<pre>item_index: 34
created_at: 2011-12-23 18:03:05
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: BrowserID hangs on &quot;Communicating with server&quot; on iPad (iOS5)
body:
@jmathai wait, laptop or ipad?

Since we&#x27;re not able to replicate this at all, it&#x27;s not clear what parameters could be at stake.... maybe a wedged localStorage? But we&#x27;re pretty aggressive about clearing that when things go wrong. We&#x27;ll keep an eye on this. I&#x27;ll leave this bug open a few more days to see if we can reproduce it.</pre>

<pre>item_index: 35
created_at: 2011-12-23 03:21:17
event_type: PullRequestEvent
repo_name: mozilla/browserid
title: Feature randomseed from server
body:
None</pre>

<pre>item_index: 36
created_at: 2011-12-23 03:19:27
event_type: IssuesEvent
repo_name: mozilla/browserid
title: entropy on all devices, in particular touch
body:
need to review the randomness approach on all devices, in particular touch devices where there is no user input to seed the PRNG.</pre>

<pre>item_index: 37
created_at: 2011-12-23 00:24:36
event_type: IssuesEvent
repo_name: mozilla/browserid
title: fix csrf token generation
body:
None</pre>

<pre>item_index: 38
created_at: 2011-12-23 00:20:29
event_type: IssuesEvent
repo_name: mozilla/browserid
title: fix csrf token generation
body:
None</pre>

<pre>item_index: 39
created_at: 2011-12-23 00:07:31
event_type: IssueCommentEvent
repo_name: mozilla/browserid
title: BrowserID hangs on &quot;Communicating with server&quot; on iPad (iOS5)
body:
@jmathai I&#x27;m not able to reproduce this on ipad 5.0.1 here. Can you check if this is still an issue? Are you able to reproduce this on more than one ipad (I know, tough question if you only have one.)</pre>

<pre>item_index: 40
created_at: 2011-12-22 15:26:09
event_type: IssuesEvent
repo_name: benadida/helios-server
title: Private elections require trustees to be logged in as voters to submit decryptions
body:
If a trustee is not also a voter in a private election (or happens to not be logged in as a voter), they will be unable to submit decryption results [getting a 302 when attempting to POST to https://www.foo.tld/voting/helios/elections/UUID/trustees/UUID/upload-decryption to a page that would ask them to authenticate to view the election]. Worse yet, this fails silently and appears to claim that uploading the partial decryption was successful rather than displaying an error; since the POST is done as an AJAX call, nobody sees the login page.</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      14,
      20,
      29,
      36,
      40
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;security&quot;,
    &quot;citations&quot;: [
      1,
      7,
      8,
      14,
      20,
      21,
      33,
      36,
      37,
      38
    ],
    &quot;description&quot;: &quot;Security hardening of Mozilla BrowserID identity system: cookie encryption and signing, CSRF token generation, POST body size limits, entropy on touch devices, and fixing security holes in account email addition.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      9,
      11,
      18,
      22,
      25,
      27,
      28,
      31,
      32,
      33,
      34
    ],
    &quot;value&quot;: &quot;leading&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      9,
      14,
      20,
      29,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      29,
      35,
      40
    ],
    &quot;value&quot;: 1
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      3,
      15,
      19,
      24,
      29,
      35
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      14,
      20,
      29,
      33,
      36,
      37,
      40
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 33: `arihanv` — `2024-07-01`

Items in bundle: 36

### Bundle text

<pre>item_index: 1
created_at: 2024-07-29 06:02:33
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: markdown
body:
![Screenshot 2024-07-29 at 1 02 17 AM](https://github.com/user-attachments/assets/a23bffcc-2cd1-438f-9a49-59ad54608387)
</pre>

<pre>item_index: 2
created_at: 2024-07-29 06:02:26
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: markdown
body:
![Screenshot 2024-07-29 at 1 02 17 AM](https://github.com/user-attachments/assets/a23bffcc-2cd1-438f-9a49-59ad54608387)
</pre>

<pre>item_index: 3
created_at: 2024-07-29 05:57:01
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: nav
body:
![Screenshot 2024-07-29 at 12 55 58 AM](https://github.com/user-attachments/assets/944bbd23-001f-4a72-a371-6700a2698092)
</pre>

<pre>item_index: 4
created_at: 2024-07-29 05:56:54
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: nav
body:
![Screenshot 2024-07-29 at 12 55 58 AM](https://github.com/user-attachments/assets/944bbd23-001f-4a72-a371-6700a2698092)
</pre>

<pre>item_index: 5
created_at: 2024-07-29 04:43:09
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: form + label
body:
![Screenshot 2024-07-28 at 11 42 29 PM](https://github.com/user-attachments/assets/52a07b49-e742-432d-8fb9-76cc6b1a8495)
</pre>

<pre>item_index: 6
created_at: 2024-07-29 04:42:59
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: form + label
body:
![Screenshot 2024-07-28 at 11 42 29 PM](https://github.com/user-attachments/assets/52a07b49-e742-432d-8fb9-76cc6b1a8495)
</pre>

<pre>item_index: 7
created_at: 2024-07-29 04:25:20
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: grid
body:
None</pre>

<pre>item_index: 8
created_at: 2024-07-29 04:24:50
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: grid
body:
None</pre>

<pre>item_index: 9
created_at: 2024-07-29 02:56:19
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: update: card hover effects
body:
![Screenshot 2024-07-28 at 9 53 46 PM](https://github.com/user-attachments/assets/6247450f-6b82-4bc6-8a11-f3db941862a6)
</pre>

<pre>item_index: 10
created_at: 2024-07-29 02:53:57
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: update: card hover effects
body:
![Screenshot 2024-07-28 at 9 53 46 PM](https://github.com/user-attachments/assets/6247450f-6b82-4bc6-8a11-f3db941862a6)
</pre>

<pre>item_index: 11
created_at: 2024-07-29 02:47:37
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: card
body:
![Screenshot 2024-07-28 at 9 47 20 PM](https://github.com/user-attachments/assets/f6cda1fd-729c-4a5c-82bd-4ad87a88a3dc)
</pre>

<pre>item_index: 12
created_at: 2024-07-29 02:47:29
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: card
body:
![Screenshot 2024-07-28 at 9 47 20 PM](https://github.com/user-attachments/assets/f6cda1fd-729c-4a5c-82bd-4ad87a88a3dc)
</pre>

<pre>item_index: 13
created_at: 2024-07-29 02:41:13
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: stack
body:
![Screenshot 2024-07-28 at 9 40 55 PM](https://github.com/user-attachments/assets/51525d61-b115-45f5-9d25-c237c6001a1a)
</pre>

<pre>item_index: 14
created_at: 2024-07-29 02:41:05
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: stack
body:
![Screenshot 2024-07-28 at 9 40 55 PM](https://github.com/user-attachments/assets/51525d61-b115-45f5-9d25-c237c6001a1a)
</pre>

<pre>item_index: 15
created_at: 2024-07-28 06:42:26
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: link
body:
None</pre>

<pre>item_index: 16
created_at: 2024-07-28 06:41:30
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: link
body:
None</pre>

<pre>item_index: 17
created_at: 2024-07-28 05:35:58
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: image
body:
None</pre>

<pre>item_index: 18
created_at: 2024-07-28 05:35:39
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: image
body:
None</pre>

<pre>item_index: 19
created_at: 2024-07-28 01:10:12
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: calendar
body:
![image](https://github.com/user-attachments/assets/fa01ccc3-cf4b-4253-a8e2-14a60e52926d)
</pre>

<pre>item_index: 20
created_at: 2024-07-28 01:09:04
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: calendar
body:
![image](https://github.com/user-attachments/assets/fa01ccc3-cf4b-4253-a8e2-14a60e52926d)
</pre>

<pre>item_index: 21
created_at: 2024-07-28 00:00:25
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: popover
body:
![Screenshot 2024-07-27 at 6 59 02 PM](https://github.com/user-attachments/assets/96fa1f34-f27f-4183-9f7c-de5cceec5477)
</pre>

<pre>item_index: 22
created_at: 2024-07-27 23:59:14
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: popover
body:
![Screenshot 2024-07-27 at 6 59 02 PM](https://github.com/user-attachments/assets/96fa1f34-f27f-4183-9f7c-de5cceec5477)
</pre>

<pre>item_index: 23
created_at: 2024-07-27 23:54:11
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: modal
body:
![Screenshot 2024-07-27 at 6 53 24 PM](https://github.com/user-attachments/assets/648b3e77-dcb6-4578-a109-a31b0a71f493)
</pre>

<pre>item_index: 24
created_at: 2024-07-27 23:53:58
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: modal
body:
![Screenshot 2024-07-27 at 6 53 24 PM](https://github.com/user-attachments/assets/648b3e77-dcb6-4578-a109-a31b0a71f493)
</pre>

<pre>item_index: 25
created_at: 2024-07-27 23:31:25
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: select
body:
![Screenshot 2024-07-27 at 6 23 57 PM](https://github.com/user-attachments/assets/cf5fbbc5-f6a1-40b0-b790-e718e44cb02e)
</pre>

<pre>item_index: 26
created_at: 2024-07-27 23:24:15
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: select
body:
![Screenshot 2024-07-27 at 6 23 57 PM](https://github.com/user-attachments/assets/cf5fbbc5-f6a1-40b0-b790-e718e44cb02e)
</pre>

<pre>item_index: 27
created_at: 2024-07-25 20:17:25
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: context menu
body:
&lt;img width=&quot;712&quot; alt=&quot;Screenshot 2024-07-25 at 3 15 00 PM&quot; src=&quot;https://github.com/user-attachments/assets/e7561ce8-33a7-4a29-8188-3d983a6646d8&quot;&gt;
</pre>

<pre>item_index: 28
created_at: 2024-07-25 20:15:40
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: context menu
body:
&lt;img width=&quot;712&quot; alt=&quot;Screenshot 2024-07-25 at 3 15 00 PM&quot; src=&quot;https://github.com/user-attachments/assets/e7561ce8-33a7-4a29-8188-3d983a6646d8&quot;&gt;
</pre>

<pre>item_index: 29
created_at: 2024-07-25 04:52:45
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: codeblock
body:
&lt;img width=&quot;579&quot; alt=&quot;Screenshot 2024-07-24 at 11 39 36 PM&quot; src=&quot;https://github.com/user-attachments/assets/bf75445a-8611-4c39-8cd4-a2fa81aa828e&quot;&gt;
</pre>

<pre>item_index: 30
created_at: 2024-07-25 04:39:50
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: codeblock
body:
&lt;img width=&quot;579&quot; alt=&quot;Screenshot 2024-07-24 at 11 39 36 PM&quot; src=&quot;https://github.com/user-attachments/assets/bf75445a-8611-4c39-8cd4-a2fa81aa828e&quot;&gt;
</pre>

<pre>item_index: 31
created_at: 2024-07-25 03:55:29
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: upload
body:
&lt;img width=&quot;273&quot; alt=&quot;Screenshot 2024-07-24 at 10 54 58 PM&quot; src=&quot;https://github.com/user-attachments/assets/ede7bcea-4f5c-4f55-9446-da0e9781d56c&quot;&gt;
</pre>

<pre>item_index: 32
created_at: 2024-07-25 03:55:04
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: upload
body:
&lt;img width=&quot;273&quot; alt=&quot;Screenshot 2024-07-24 at 10 54 58 PM&quot; src=&quot;https://github.com/user-attachments/assets/ede7bcea-4f5c-4f55-9446-da0e9781d56c&quot;&gt;
</pre>

<pre>item_index: 33
created_at: 2024-07-25 03:44:02
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: accordion
body:
&lt;img width=&quot;450&quot; alt=&quot;Screenshot 2024-07-24 at 10 43 11 PM&quot; src=&quot;https://github.com/user-attachments/assets/ef388f0a-736c-4de7-be96-0631960d06d2&quot;&gt;
</pre>

<pre>item_index: 34
created_at: 2024-07-25 03:43:32
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: accordion
body:
&lt;img width=&quot;450&quot; alt=&quot;Screenshot 2024-07-24 at 10 43 11 PM&quot; src=&quot;https://github.com/user-attachments/assets/ef388f0a-736c-4de7-be96-0631960d06d2&quot;&gt;
</pre>

<pre>item_index: 35
created_at: 2024-07-25 03:36:04
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: badge
body:
&lt;img width=&quot;339&quot; alt=&quot;Screenshot 2024-07-24 at 10 35 17 PM&quot; src=&quot;https://github.com/user-attachments/assets/80d70261-e867-4b50-a27d-265526f2aa8e&quot;&gt;
</pre>

<pre>item_index: 36
created_at: 2024-07-25 03:35:50
event_type: PullRequestEvent
repo_name: RubricLab/ui
title: feat: badge
body:
&lt;img width=&quot;339&quot; alt=&quot;Screenshot 2024-07-24 at 10 35 17 PM&quot; src=&quot;https://github.com/user-attachments/assets/80d70261-e867-4b50-a27d-265526f2aa8e&quot;&gt;
</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;description&quot;: &quot;Building a UI component library (RubricLab/ui) with individual component PRs for markdown, nav, form, grid, card, stack, link, image, calendar, popover, modal, select, context menu, codeblock, upload, accordion, and badge.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      9,
      11,
      13,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: 2
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      5,
      7,
      9,
      11,
      13,
      15,
      17,
      19,
      21,
      23,
      25,
      27,
      29,
      31,
      33,
      35
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 34: `danielbarter` — `2024-01-01`

Items in bundle: 20

### Bundle text

<pre>item_index: 1
created_at: 2024-03-31 16:28:54
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: refind: add runtime dependencies
body:
@AndersonTorres, @chewblacka : Just a heads up, this broke cross building iso images, because sbsigntool doesn&#x27;t cross compile. The correct solution here would be to fix sbsigntool cross, but it is packaged pretty weirdly, which makes it hard. Relevant issue here: https://github.com/NixOS/nixpkgs/issues/300071

At least from my perspective, cross building iso images is pretty important, so we may need to remove the sbsigntool runtime dependency.</pre>

<pre>item_index: 2
created_at: 2024-03-29 20:20:17
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: Build failure: sbsigntool-aarch64
body:
looking through https://git.kernel.org/pub/scm/linux/kernel/git/jejb/sbsigntools.git/tree/, it seems as if ccan tools has been split out into its own repo: https://git.ozlabs.org/?p=ccan, so we may want to build that separately. </pre>

<pre>item_index: 3
created_at: 2024-03-29 20:05:24
event_type: IssuesEvent
repo_name: NixOS/nixpkgs
title: Build failure: sbsigntool-aarch64
body:
### Steps To Reproduce

Steps to reproduce the behavior:
`nix-build -E &#x27;with import /path/to/nixpkgs {}; pkgsCross.aarch64-multiplatform.sbsigntool&#x27;`

### Build log

```
@nix { &quot;action&quot;: &quot;setPhase&quot;, &quot;phase&quot;: &quot;unpackPhase&quot; }
Running phase: unpackPhase
unpacking source archive /nix/store/y149xplgdgi3n7jivjfz1x8fg9f140r3-sbsigntools
source root is sbsigntools
@nix { &quot;action&quot;: &quot;setPhase&quot;, &quot;phase&quot;: &quot;patchPhase&quot; }
Running phase: patchPhase
patching script interpreter paths in .
./autogen.sh: interpreter directive changed from &quot;#!/bin/bash&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash&quot;
./tests/sign-invalidattach-verify.sh: interpreter directive changed from &quot;#!/bin/bash -e&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash -e&quot;
./tests/sign-attach-verify.sh: interpreter directive changed from &quot;#!/bin/bash -e&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash -e&quot;
./tests/detach-remove.sh: interpreter directive changed from &quot;#!/bin/bash -ex&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash -ex&quot;
./tests/sign-missing-cert.sh: interpreter directive changed from &quot;#!/bin/bash -e&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash -e&quot;
./tests/reattach-warning.sh: interpreter directive changed from &quot;#!/bin/bash -e&quot; to &quot;/nix/store/5lr5n3qa4day8l1ivbwlcby2nknczqkq-bash-5.2p26/bin/bash -e&quot;
./tests/cert-table-header.sh: interpreter directive changed from &quot;#!/bin/bash -e&quot; to &quot;/n</pre>

<pre>item_index: 4
created_at: 2024-03-29 15:45:49
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: resholve: 0.9.1 -&gt; 0.10.2, ongoing cross fixes
body:
yep, after rebasing this into staging, both `lesspipe` and `xdg-utils` build.</pre>

<pre>item_index: 5
created_at: 2024-03-27 03:55:58
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: Build failure: xdg-utils (aarch64-linux cross)
body:
@abathur: 

With https://github.com/NixOS/nixpkgs/pull/298515 and https://github.com/NixOS/nixpkgs/pull/298001, I am still seeing issues with cross compiling `xdg-utils`:

```
Running phase: fixupPhase
[resholve context] : invoking resholve with PWD=/nix/store/b4dz07ykwb1vhvrpmwsn8q77rwvn4hg1-xdg-utils-aarch64-unknown-linux-gnu-1.2.1
[resholve context] RESHOLVE_LORE=/nix/store/1qz3ic8lv3sfdn42mdb99rsby6mma2ws-more-binlore
[resholve context] RESHOLVE_EXECER=cannot:/nix/store/icwsjb8xj0l6xaqiar55chysha6f0q8c-xdg-user-dirs-aarch64-unknown-linux-gnu-0.18/bin/xdg-user-dir
[resholve context] RESHOLVE_FAKE=&#x27;external:&#x27;\&#x27;&#x27;explorer.exe&#x27;\&#x27;&#x27;;&#x27;\&#x27;&#x27;gnome-default-applications-properties&#x27;\&#x27;&#x27;;&#x27;\&#x27;&#x27;kde-config&#x27;\&#x27;&#x27;;&#x27;\&#x27;&#x27;xprop&#x27;\&#x27;&#x27;;&#x27;\&#x27;&#x27;gconftool-2&#x27;\&#x27;&#x27;&#x27;
[resholve context] RESHOLVE_INPUTS=/nix/store/11l9nr6di5dl98kncc128dq1c45dq4ha-dbus-aarch64-unknown-linux-gnu-1.14.10/bin:/nix/store/r1i320xwdhd7mkj38xhzakfir5nb1fda-coreutils-aarch64-unknown-linux-gnu-9.4/bin:/nix/store/vyw8s4fljapy9gklsgxlgsjxj5dsgfd1-gnugrep-aarch64-unknown-linux-gnu-3.11/bin:/nix/store/clmi4bhi11gs0qhikn26d8xm32dgbjm1-gnused-aarch64-unknown-linux-gnu-4.9/bin:/nix/store/icwsjb8xj0l6xaqiar55chysha6f0q8c-xdg-user-dirs-aarch64-unknown-linux-gnu-0.18/bin
[resholve context] RESHOLVE_INTERPRETER=/nix/store/xhz88dqwv29wkn3xnyin6qsh2lk48yd6-bash-aarch64-unknown-linux-gnu-5.2p26/bin/bash
[resholve context] RESHOLVE_KEEP=&#x27;$KDE_SESSION_VERSION&#x27;
[resholve context] RESHOLVE_PROLOGUE=/nix/store/y5xn5jmgjkcj4ilswshxrfga21as2mj1-xdg-ut</pre>

<pre>item_index: 6
created_at: 2024-03-27 03:49:44
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: lesspipe: cross-compilation regressed
body:
Can confirm that lesspipe cross compiling is working with https://github.com/NixOS/nixpkgs/pull/298515 and https://github.com/NixOS/nixpkgs/pull/298001. `xdg-utils` is still having issues though. Will ping abathur in the corresponding issue.</pre>

<pre>item_index: 7
created_at: 2024-03-27 00:05:25
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: xdg-utils: fix cross-compilation
body:
Just so everyone is on the same page here, @abathur is very close to having resholve working for cross https://github.com/NixOS/nixpkgs/pull/298515. He may have jumped the gun a little with migrating some of these deeper packages, but IMO the approach is gonna be better in the long run, because it is more reliable at catching all the places that need to be patched.</pre>

<pre>item_index: 8
created_at: 2024-03-26 22:51:25
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: lesspipe: cross-compilation regressed
body:
@abathur:

its not fixed on your branch, because gnupg is failing to build for a completely unrelated reason: https://github.com/NixOS/nixpkgs/pull/298001

should be good with both commits though.</pre>

<pre>item_index: 9
created_at: 2024-03-24 17:12:08
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: gnupg: fix cross compilation
body:
Tested using 
nix-build -E `with import /path/to/nixpkgs {}; pkgsCross.aarch64-multiplatform.gnupg.override { enableMinimal = true;}&#x27;
and everything looks good.</pre>

<pre>item_index: 10
created_at: 2024-03-23 17:04:28
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: resholve: 0.9.1 -&gt; 0.10.1, ongoing cross fixes
body:
@abathur: Can you rebase onto staging so that I can test this in combination with some of the other recent cross fixes (e.g procmail)? </pre>

<pre>item_index: 11
created_at: 2024-03-23 00:52:54
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: resholve: 0.9.1 -&gt; 0.10.0, ongoing cross fixes
body:
Yep, it is still building. </pre>

<pre>item_index: 12
created_at: 2024-03-22 22:00:45
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: resholve: 0.9.1 -&gt; 0.10.0, ongoing cross fixes
body:
This fixes building `pkgsCross.aarch64-multiplatform.lesspipe` :sunglasses: </pre>

<pre>item_index: 13
created_at: 2024-03-15 14:36:39
event_type: IssueCommentEvent
repo_name: danielbarter/mini_compile_commands
title: `compile_commands.json` is not generate - what am I doing wrong?
body:
When you spawn a dev shell, no building actually happens (so no compiler invocations occur). It puts you into an environment where you can build. 

In you dev shell, if you launch the mini compile commands server and then build your project, a `compile_commands.json` will be created </pre>

<pre>item_index: 14
created_at: 2024-03-11 18:43:54
event_type: IssueCommentEvent
repo_name: danielbarter/mini_compile_commands
title: Unable to find C++ standard library when used with GCC
body:
At some point, I expect nixpkgs to split gcc up into smaller packages. When that happens, this project will need to be updated accordingly. 

</pre>

<pre>item_index: 15
created_at: 2024-03-04 18:16:27
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: ostree: version bump and fix aarch64 cross compilation
body:
Actually, cross compiling issues seem to already be fixed on master anyway. </pre>

<pre>item_index: 16
created_at: 2024-03-04 18:13:30
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: Build failure: ostree-aarch64-unknown-linux-gnu-2023.2
body:
@skyrgobbler: PR which fixes issue https://github.com/NixOS/nixpkgs/pull/293303</pre>

<pre>item_index: 17
created_at: 2024-03-04 18:09:43
event_type: PullRequestEvent
repo_name: NixOS/nixpkgs
title: ostree: version bump and fix aarch64 cross compilation
body:
Addressing https://github.com/NixOS/nixpkgs/issues/249177. Bumping version of ostree, which also fixes cross compilation.

&lt;!--
For package updates please link to a changelog or describe changes, this helps your fellow maintainers discover breaking updates.
For new packages please briefly describe the package or provide a link to its homepage.
--&gt;

- bumped version
- removed old patches (which don&#x27;t seem to be needed anymore)

&lt;!-- Please check what applies. Note that these are not hard requirements but merely serve as information for reviewers. --&gt;

- Built on platform(s)
  - [x] x86_64-linux
  - [x] aarch64-linux
  - [ ] x86_64-darwin
  - [ ] aarch64-darwin
- For non-Linux: Is sandboxing enabled in `nix.conf`? (See [Nix manual](https://nixos.org/manual/nix/stable/command-ref/conf-file.html))
  - [ ] `sandbox = relaxed`
  - [ ] `sandbox = true`
- [ ] Tested, as applicable:
  - [NixOS test(s)](https://nixos.org/manual/nixos/unstable/index.html#sec-nixos-tests) (look inside [nixos/tests](https://github.com/NixOS/nixpkgs/blob/master/nixos/tests))
  - and/or [package tests](https://nixos.org/manual/nixpkgs/unstable/#sec-package-tests)
  - or, for functions and &quot;core&quot; functionality, tests in [lib/tests](https://github.com/NixOS/nixpkgs/blob/master/lib/tests) or [pkgs/test](https://github.com/NixOS/nixpkgs/blob/master/pkgs/test)
  - made sure NixOS tests are [linked](https://nixos.org/manual/nixpkgs/unstable/#ssec-nixos-tests-linking) to the relevant packag</pre>

<pre>item_index: 18
created_at: 2024-03-04 05:10:52
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: Build failure: ostree-aarch64-unknown-linux-gnu-2023.2
body:
Confirmed. Seems like this is a python distutils issue. Somehow, it is trying to run `gcc` instead of whatever compiler is in `$CC`. Since distutils has been depreciated since python 3.12, this may be fixed by updating ostree, since the version we have in nixpkgs is a year out of date.</pre>

<pre>item_index: 19
created_at: 2024-01-15 20:56:21
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: networkd just stops managing my wlan0 after some generation changes
body:
I run sway, networks, iwd on various lenovos and a framework laptop and haven&#x27;t encountered any of the issues mentioned before. Wonder if this could be hardware related?</pre>

<pre>item_index: 20
created_at: 2024-01-02 05:13:47
event_type: IssueCommentEvent
repo_name: NixOS/nixpkgs
title: cupsd: allow cups package override
body:
@SuperSandro2000: this should be ready to merge now</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      13,
      14,
      17,
      18
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18
    ],
    &quot;description&quot;: &quot;Fixing cross-compilation issues across multiple NixOS/nixpkgs packages (sbsigntool, lesspipe, xdg-utils, gnupg, ostree, resholve) and maintaining mini_compile_commands, a tool for generating compile_commands.json from Nix dev shells.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      4,
      7,
      8,
      10,
      16,
      20
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      13,
      17
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      13,
      17
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      13,
      14
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      9,
      17,
      18
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 35: `alshoja` — `2023-07-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2023-08-02 05:07:09
event_type: IssueCommentEvent
repo_name: PHPOffice/PHPWord
title: How to add RTL support to Html 
body:
&gt; @focaloid-dev Even though you&#x27;ve closed this, I&#x27;ve done some more thinking about it. If you can, you might want to test against my PR #2343 (updated for this issue but with unlikely to be merged any time soon). Especially have a look at the new Sample_52, which echoes your case, and now works correctly for alignment and RTL for all of Word2007, ODText, RTF, HTML, and even MPDF. At least the results look correct on my system. I&#x27;d be curious to know if they look right on yours.

Currently I pushed this thing in my project to a low priority one since it took most of my time to look around but that doesn&#x27;t mean I am not going to look into this , def this will be a high priority one after my other checklists are ove for this project , am def gona try this PR and get u back if this works or not 👏</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [],
    &quot;value&quot;: null
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: null,
    &quot;citations&quot;: [],
    &quot;description&quot;: null
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [],
    &quot;value&quot;: null
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 36: `candidosouza` — `2023-04-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2023-06-30 21:07:16
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Feat: Consolidando CategoryResource
body:
# Consolidando CategoryResource

&gt; ## Descrição

Inclua um resumo da alteração e qual problema foi corrigido. Inclua também motivação e contexto relevantes. Liste todas as dependências necessárias para essa alteração.

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e
</pre>

<pre>item_index: 2
created_at: 2023-06-30 21:06:22
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Consolidando CategoryResource
body:
# Consolidando CategoryResource

&gt; ## Descrição

Inclua um resumo da alteração e qual problema foi corrigido. Inclua também motivação e contexto relevantes. Liste todas as dependências necessárias para essa alteração.

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e
</pre>

<pre>item_index: 3
created_at: 2023-05-12 13:54:34
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Consolidando CategoryResource
body:
# Consolidando CategoryResource

&gt; ## Descrição

Inclua um resumo da alteração e qual problema foi corrigido. Inclua também motivação e contexto relevantes. Liste todas as dependências necessárias para essa alteração.

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e
</pre>

<pre>item_index: 4
created_at: 2023-05-11 14:12:47
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title:  Integração com banco de dados e Django ORM
body:
# Integração com banco de dados e Django ORM

&gt; ## Descrição

Integração com banco de dados e Django ORM

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [x] Testes Unitários
- [x] Testes de Integração
- [x] Testes e2e

</pre>

<pre>item_index: 5
created_at: 2023-05-11 14:12:25
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Integração com banco de dados e Django ORM
body:
# Integração com banco de dados e Django ORM

&gt; ## Descrição

Integração com banco de dados e Django ORM

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [x] Testes Unitários
- [x] Testes de Integração
- [x] Testes e2e

</pre>

<pre>item_index: 6
created_at: 2023-05-03 11:45:05
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Integração com banco de dados e Django ORM
body:
# Integração com banco de dados e Django ORM

&gt; ## Descrição

Integração com banco de dados e Django ORM

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [x] Testes de Integração
- [ ] Testes e2e

</pre>

<pre>item_index: 7
created_at: 2023-05-03 10:31:01
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Criando API Rest de Categoria In Memory
body:
# Criando API Rest de Categoria In Memory

&gt; ## Descrição

Criação da  API Rest de Categoria In Memory

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

- [x] Testes Unitários
- [x] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 8
created_at: 2023-05-03 10:30:24
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criando API Rest de Categoria In Memory
body:
# Criando API Rest de Categoria In Memory

&gt; ## Descrição

Criação da  API Rest de Categoria In Memory

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

- [x] Testes Unitários
- [x] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 9
created_at: 2023-04-27 22:05:05
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criando API Rest de Categoria In Memory
body:
# Criando API Rest de Categoria In Memory

&gt; ## Descrição

Criação da  API Rest de Categoria In Memory

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 10
created_at: 2023-04-27 22:04:21
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criando API Rest de Categoria In Memory
body:
# Criando API Rest de Categoria In Memory

&gt; ## Descrição

Criação da  API Rest de Categoria In Memory

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 11
created_at: 2023-04-27 20:04:23
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criando API Rest de Categoria In Memory
body:
# Criando API Rest de Categoria In Memory

&gt; ## Descrição

Criação da  API Rest de Categoria In Memory

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Testes Unitários
- [ ] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 12
created_at: 2023-04-27 20:00:02
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title:  feat: Integração do Core da aplicação com Django
body:
# Integração do Core da aplicação com Django

&gt; ## Descrição

Integrando o Django Framework com o core da aplicação

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [x] Testes Unitários
- [x] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros</pre>

<pre>item_index: 13
created_at: 2023-04-27 19:59:32
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Integração com Django
body:
# Integração do Core da aplicação com Django

&gt; ## Descrição

Integrando o Django Framework com o core da aplicação

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [x] Testes Unitários
- [x] Testes de Integração
- [ ] Testes e2e

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [x] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros</pre>

<pre>item_index: 14
created_at: 2023-04-26 21:45:40
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 15
created_at: 2023-04-26 21:45:29
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 16
created_at: 2023-04-26 21:28:04
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 17
created_at: 2023-04-26 10:38:35
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 18
created_at: 2023-04-26 10:38:26
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 19
created_at: 2023-04-26 10:38:00
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 20
created_at: 2023-04-25 13:45:11
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Casos de uso da categoria
body:
# Casos de uso da categoria

&gt; ## Descrição

Criação dos casos de uso da categoria

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Descreva os testes que você executou para verificar suas alterações. Forneça instruções para que possamos reproduzir. Liste também todos os detalhes relevantes para sua configuração de teste

- [ ] Test unitários
- [ ] Test integração

&gt; ## Checklist:

- [x] Meu código segue as diretrizes de estilo deste projeto
- [x] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [x] Testes de unidade novos e existentes passam localmente com minhas alterações
- [x] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 21
created_at: 2023-04-24 23:23:20
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criação do Repositório da Entidade Categoria
body:
# Repositório entidade Categoria

&gt; ## Descrição

Criação do Repositório da Entidade Categoria

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

- [ ] Test Unitários
- [ ] Test de Integração

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 22
created_at: 2023-04-24 23:23:09
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Criação do Repositório da Entidade Categoria
body:
# Repositório entidade Categoria

&gt; ## Descrição

Criação do Repositório da Entidade Categoria

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

- [ ] Test Unitários
- [ ] Test de Integração

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 23
created_at: 2023-04-24 23:22:25
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Repositório entidade Categoria
body:
# Repositório entidade Categoria

&gt; ## Descrição

Criação do Repositório entidade Categoria

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

- [ ] Test Unitários
- [ ] Test de Integração

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 24
created_at: 2023-04-20 12:34:49
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Develop
body:
# Atualização do README.md

&gt; ## Descrição

 Atualização do README.md

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 25
created_at: 2023-04-20 12:34:27
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Develop
body:
# Atualização do README.md

&gt; ## Descrição

 Atualização do README.md

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 26
created_at: 2023-04-20 12:30:15
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: update readme
body:
# Atualização do README.md

&gt; ## Descrição

 Atualização do README.md

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 27
created_at: 2023-04-20 12:29:57
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: update readme
body:
# Atualização do README.md

&gt; ## Descrição

 Atualização do README.md

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [x] Fiz alterações correspondentes na documentação
- [ ] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 28
created_at: 2023-04-20 12:23:34
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Observabilidade com OpenTelemetry (OTEL)
body:
# Observabilidade com OpenTelemetry (OTEL)

&gt; ## Descrição

Configurações para o uso do OpenTelemetry (OTEL) para observabilidade

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 29
created_at: 2023-04-20 12:23:23
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Observabilidade com OpenTelemetry (OTEL)
body:
# Observabilidade com OpenTelemetry (OTEL)

&gt; ## Descrição

Configurações para o uso do OpenTelemetry (OTEL) para observabilidade

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 30
created_at: 2023-04-20 12:22:56
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Observability with OpenTelemetry (OTEL)
body:
# Obiservabilidade com OpenTelemetry (OTEL)

&gt; ## Descrição

Configurações para o uso do OpenTelemetry (OTEL) para observabilidade

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 31
created_at: 2023-04-20 12:17:47
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Observability with OpenTelemetry (OTEL)
body:
# Obiservabilidade com OpenTelemetry (OTEL)

&gt; ## Descrição

Configurações para o uso do OpenTelemetry (OTEL) para observabilidade

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 32
created_at: 2023-04-19 18:40:39
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Correções e atualizações
body:
# Correções e atualizações

&gt; ## Descrição

Foi feita correções e atualização no projeto

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 33
created_at: 2023-04-19 18:39:51
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: Correções e atualizações
body:
# Correções e atualizações

&gt; ## Descrição

Foi feita correções e atualização no projeto

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 34
created_at: 2023-04-19 18:39:13
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Correções e atualizações
body:
# Correções e atualizações

&gt; ## Descrição

Foi feita correções e atualização no projeto

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 35
created_at: 2023-04-19 15:41:58
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Correções e atualizações
body:
# Correções e atualizações

&gt; ## Descrição

Foi feita correções e atualização no projeto

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 36
created_at: 2023-04-19 15:40:40
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Correções e atualizações
body:
# Correções e atualizações

&gt; ## Descrição

Foi feita correções e atualização no projeto

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 37
created_at: 2023-04-19 12:59:03
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Configuração do Prometheus, Grafana
body:
# Configuração do Prometheus, Grafana e Advisor

&gt; ## Descrição

Configurando Observabilidade  com Prometheus, Grafana e cAdvisor 

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 38
created_at: 2023-04-19 12:58:47
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: Configuração do Prometheus, Grafana
body:
# Configuração do Prometheus, Grafana e Advisor

&gt; ## Descrição

Configurando Observabilidade  com Prometheus, Grafana e cAdvisor 

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 39
created_at: 2023-04-19 12:58:14
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: observability with prometheus
body:
# Configuração do Prometheus, Grafana e Advisor

&gt; ## Descrição

Configurando Observabilidade  com Prometheus, Grafana e cAdvisor 

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

<pre>item_index: 40
created_at: 2023-04-19 02:33:14
event_type: PullRequestEvent
repo_name: candidosouza/fc_admin_codeflix_python
title: feat: observability with prometheus
body:
# Configuração do Prometheus, Grafana e Advisor

&gt; ## Descrição

Configurando Observabilidade  com Prometheus, Grafana e cAdvisor 

Fixes # (issue)

&gt; ## Tipo de mudança

- [ ] Correção de bug (alteração ininterrupta que corrige um problema)
- [x] Novo recurso (alteração ininterrupta que adiciona funcionalidade)
- [ ] Alteração de última hora (correção ou recurso que faria com que a funcionalidade existente não funcionasse conforme o esperado)
- [ ] Esta alteração requer uma atualização de documentação

&gt; ## Como isso foi testado?

Tarefa não necessita de testes

&gt; ## Checklist:

- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Realizei uma autorrevisão do meu próprio código
- [ ] Comentei meu código, principalmente em áreas difíceis de entender
- [ ] Fiz alterações correspondentes na documentação
- [x] Minhas alterações não geram novos avisos
- [ ] Adicionei testes que provam que minha correção é eficaz ou que meu recurso funciona
- [ ] Testes de unidade novos e existentes passam localmente com minhas alterações
- [ ] Quaisquer alterações dependentes foram mescladas e publicadas em módulos downstream
- [ ] Eu verifiquei meu código e corrigi todos os erros ortográficos
</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      28,
      29,
      30,
      31,
      37,
      38,
      39,
      40
    ],
    &quot;description&quot;: &quot;Django-based admin application with REST API for category management, database integration via Django ORM, and observability tooling (OpenTelemetry, Prometheus, Grafana).&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      28,
      29,
      30,
      31,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: 2
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: 1
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      19,
      20,
      21,
      22,
      23,
      28,
      29,
      30,
      31,
      37,
      38,
      39,
      40
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 37: `adammakuchowski` — `2023-04-01`

Items in bundle: 40

### Bundle text

<pre>item_index: 1
created_at: 2023-06-30 18:06:59
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco
title: init CheckoutHeader
body:
None</pre>

<pre>item_index: 2
created_at: 2023-06-30 18:06:33
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco
title: init CheckoutHeader
body:
None</pre>

<pre>item_index: 3
created_at: 2023-06-30 16:58:55
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco
title: moved buttons and cards to common components
body:
None</pre>

<pre>item_index: 4
created_at: 2023-06-30 16:58:27
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco
title: moved buttons and cards to common components
body:
None</pre>

<pre>item_index: 5
created_at: 2023-06-28 19:11:06
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: changed project name
body:
None</pre>

<pre>item_index: 6
created_at: 2023-06-28 19:10:54
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: changed project name
body:
None</pre>

<pre>item_index: 7
created_at: 2023-06-27 17:43:08
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init basic checkout routing
body:
None</pre>

<pre>item_index: 8
created_at: 2023-06-27 17:42:53
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init basic checkout routing
body:
None</pre>

<pre>item_index: 9
created_at: 2023-06-26 15:34:02
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update missing type
body:
None</pre>

<pre>item_index: 10
created_at: 2023-06-26 15:33:52
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update missing type
body:
None</pre>

<pre>item_index: 11
created_at: 2023-06-25 12:35:16
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update products data
body:
None</pre>

<pre>item_index: 12
created_at: 2023-06-25 12:34:56
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update products data
body:
None</pre>

<pre>item_index: 13
created_at: 2023-06-24 13:08:50
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: fix productGallery card active action
body:
None</pre>

<pre>item_index: 14
created_at: 2023-06-24 13:07:53
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: fix productGallery card active action
body:
None</pre>

<pre>item_index: 15
created_at: 2023-06-23 19:24:17
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update productGallery navigation
body:
None</pre>

<pre>item_index: 16
created_at: 2023-06-23 19:23:13
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update productGallery navigation
body:
None</pre>

<pre>item_index: 17
created_at: 2023-06-21 17:37:18
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init summary ProductCart
body:
None</pre>

<pre>item_index: 18
created_at: 2023-06-20 18:07:35
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update addToCart reducer - productSilce
body:
None</pre>

<pre>item_index: 19
created_at: 2023-06-20 18:07:00
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update addToCart reducer - productSilce
body:
None</pre>

<pre>item_index: 20
created_at: 2023-06-19 18:02:27
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: initRemoveProductCart-reducer
body:
None</pre>

<pre>item_index: 21
created_at: 2023-06-19 18:01:21
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: initRemoveProductCart-reducer
body:
None</pre>

<pre>item_index: 22
created_at: 2023-06-18 12:32:06
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init updateQuantityProductCart
body:
None</pre>

<pre>item_index: 23
created_at: 2023-06-18 12:31:41
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init updateQuantityProductCart
body:
None</pre>

<pre>item_index: 24
created_at: 2023-06-17 14:28:18
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init incrementQuantityProductCart
body:
None</pre>

<pre>item_index: 25
created_at: 2023-06-17 14:27:32
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init incrementQuantityProductCart
body:
None</pre>

<pre>item_index: 26
created_at: 2023-06-16 15:41:04
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry component content
body:
None</pre>

<pre>item_index: 27
created_at: 2023-06-16 15:22:11
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry component content
body:
None</pre>

<pre>item_index: 28
created_at: 2023-06-15 17:40:00
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry header
body:
None</pre>

<pre>item_index: 29
created_at: 2023-06-15 17:39:43
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry header
body:
None</pre>

<pre>item_index: 30
created_at: 2023-06-14 15:53:59
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update missing useState type
body:
None</pre>

<pre>item_index: 31
created_at: 2023-06-14 15:53:48
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update missing useState type
body:
None</pre>

<pre>item_index: 32
created_at: 2023-06-13 16:14:06
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update active ProductCard action
body:
None</pre>

<pre>item_index: 33
created_at: 2023-06-12 17:24:57
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update product cart scroll
body:
None</pre>

<pre>item_index: 34
created_at: 2023-06-11 15:19:37
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry
body:
None</pre>

<pre>item_index: 35
created_at: 2023-06-11 15:19:19
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update ProductCartEntry
body:
None</pre>

<pre>item_index: 36
created_at: 2023-06-10 13:34:37
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init ProductCartEntry component
body:
None</pre>

<pre>item_index: 37
created_at: 2023-06-10 13:34:16
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: init ProductCartEntry component
body:
None</pre>

<pre>item_index: 38
created_at: 2023-06-09 20:12:46
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: deleted unused photos
body:
None</pre>

<pre>item_index: 39
created_at: 2023-06-09 20:12:35
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: deleted unused photos
body:
None</pre>

<pre>item_index: 40
created_at: 2023-06-08 11:34:57
event_type: PullRequestEvent
repo_name: adammakuchowski/corvo-bianco-web
title: update icon button component
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: &quot;self&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;application&quot;,
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;description&quot;: &quot;Building a web e-commerce application (&#x27;corvo-bianco&#x27;) with product gallery, shopping cart, and checkout features using React and Redux.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: 3
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      3,
      7,
      11,
      17,
      18,
      36
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 38: `alyx` — `2011-04-01`

Items in bundle: 1

### Bundle text

<pre>item_index: 1
created_at: 2011-06-15 00:40:56
event_type: PullRequestEvent
repo_name: pirogoeth/labere
title: Make this be right.
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;other&quot;,
    &quot;citations&quot;: [
      1
    ],
    &quot;description&quot;: &quot;A pull request titled &#x27;Make this be right.&#x27; submitted to the repo pirogoeth/labere, with no body or descriptive context to determine the project&#x27;s purpose.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: &quot;contributing&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 1
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 39: `changhiskhan` — `2013-01-01`

Items in bundle: 7

### Bundle text

<pre>item_index: 1
created_at: 2013-03-29 16:36:17
event_type: PullRequestEvent
repo_name: pydata/pandas
title: BUG: stacking with MultiIndex column with some unused level uniques fail...
body:
...s #3170</pre>

<pre>item_index: 2
created_at: 2013-03-29 06:00:52
event_type: PullRequestEvent
repo_name: pydata/pandas
title: BUG: anchored week to_timestamp conversion run #2742
body:
threshold set wrong in get_to_timestamp_base</pre>

<pre>item_index: 3
created_at: 2013-03-29 04:51:36
event_type: PullRequestEvent
repo_name: pydata/pandas
title: BUG: DatetimeIndex bug adding offsets to tz-aware indices #3210
body:
and some PEP8 cleanup</pre>

<pre>item_index: 4
created_at: 2013-03-18 06:11:15
event_type: PullRequestEvent
repo_name: pydata/pandas
title: Int bug
body:
slightly different fix for #3071</pre>

<pre>item_index: 5
created_at: 2013-02-09 23:04:59
event_type: PullRequestEvent
repo_name: pydata/pandas
title: BUG: Period/DateTime slicing and setitem fixes (fixes #2782, #2788, #2789)
body:
fixes #2782

simple fix...can&#x27;t see any reason why the original code was doing what it was, especially since indices are immutable

added test coverage in test_series.py</pre>

<pre>item_index: 6
created_at: 2013-01-22 04:19:18
event_type: PullRequestEvent
repo_name: pydata/pandas
title: mysql support
body:
I added mysql support and (untested!) support for oracle. Some parts of the code are ready to support other flavors -- it should be easy to extend.</pre>

<pre>item_index: 7
created_at: 2013-01-03 20:24:18
event_type: PullRequestEvent
repo_name: pydata/pandas
title: BUG: Series op with datetime64 values misbehaves in numpy 1.6 #2629
body:
converts to i8 then back to timedelta64[ns] if both datetime64</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      5,
      6
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;data_ai&quot;,
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      6,
      7
    ],
    &quot;description&quot;: &quot;Bug fixes and feature additions to the pandas data analysis library, including datetime/index handling, SQL database support, and Series operations.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      5,
      6
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3,
      5,
      6,
      7
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      5,
      6,
      7
    ],
    &quot;value&quot;: 2
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>

## Bundle 40: `aleandros` — `2014-01-01`

Items in bundle: 3

### Bundle text

<pre>item_index: 1
created_at: 2014-03-02 02:14:07
event_type: PullRequestEvent
repo_name: aleandros/what_now
title: Make regex case-insensitive
body:
This makes the regex case-insensitive for the future, so that it matches TODO&#x27;s in both lowercase (`todo`) and mixed case (`Todo`).</pre>

<pre>item_index: 2
created_at: 2014-03-01 16:08:14
event_type: PullRequestEvent
repo_name: aleandros/what_now
title: Simplify the search regex
body:
This one is a bit simpler and thus probably slightly more performant.</pre>

<pre>item_index: 3
created_at: 2014-03-01 02:31:26
event_type: PullRequestEvent
repo_name: aleandros/what_now
title: Add a space in the README for readability
body:
None</pre>

### Model annotation

<pre>{
  &quot;audience_orientation&quot;: {
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;value&quot;: &quot;developers&quot;
  },
  &quot;building_what&quot;: {
    &quot;category&quot;: &quot;developer_tool&quot;,
    &quot;citations&quot;: [
      1,
      2
    ],
    &quot;description&quot;: &quot;A tool that searches for and matches TODO comments in code, with regex-based pattern matching.&quot;
  },
  &quot;collaboration_posture&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: &quot;solo&quot;
  },
  &quot;commercial_language&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 0
  },
  &quot;domain_shift&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 0
  },
  &quot;productization_markers&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 0
  },
  &quot;seriousness&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;value&quot;: 0
  },
  &quot;stated_founding_intent&quot;: {
    &quot;citations&quot;: [
      1,
      2,
      3
    ],
    &quot;quote&quot;: null,
    &quot;value&quot;: &quot;none&quot;
  }
}</pre>


## Blind review results

Independent blind re-annotation of all 40 bundles by a second rater (Claude, 2026-07-19), compared against the GLM-5.2 annotations in `data/semantics/annotations.parquet` (joined on `actor_login` + `quarter`; all 40 matched).

### Protocol notes

- The sample file interleaves `### Model annotation` blocks with bundle text. Before reading any bundle past the first, all model-annotation sections were mechanically stripped into a text-only copy (`grep`-based script), and the blind pass was done exclusively on that copy. Model outputs were loaded only after all 40 ratings were recorded. For bundle 01 the top of the original file was read before extraction, but the read window ended before its model-annotation block, so it stayed blind too. Full protocol adherence.
- Important caveat: the sample file contains only CURRENT QUARTER text, while the model prompt also received EARLIER CONTEXT bundles for the `domain_shift` comparison. The blind rater therefore defaulted `domain_shift` to 0 in nearly every bundle. The `domain_shift` row below measures a protocol artifact more than instrument quality; regenerate the sample with earlier-context excerpts before drawing conclusions on that field.

### Per-field agreement (n = 40)

| Field | Exact | Within-1 | Bias (model − rater) | Verdict |
|---|---|---|---|---|
| building_what_category | 26/40 (65%) | — | model over-uses `developer_tool` (10/14 disagreements) | MERGE/REVISE |
| audience_orientation | 24/40 (60%) | — | model favors `developers`/`self`; rater's `end_users`/`customers` rarely reproduced | MERGE/REVISE |
| productization_markers | 26/40 (65%) | 40/40 (100%) | +0.00 (symmetric 1-step noise) | KEEP |
| commercial_language | 39/40 (98%) | 40/40 (100%) | +0.03 | KEEP |
| collaboration_posture | 24/40 (60%) | — | model favors `solo` where rater saw `leading` (maintainer-with-community bundles) | MERGE/REVISE |
| stated_founding_intent | 35/40 (88%) | — | model over-triggers `implicit` on ordinary side-project publishing; missed org/venture context twice | KEEP |
| seriousness | 24/40 (60%) | 40/40 (100%) | −0.20 (model compresses the top: 6 of rater's 3s scored 2) | KEEP |
| domain_shift | 19/40 (48%) | 32/40 (80%) | +0.80 (confounded: rater lacked earlier context) | MERGE/REVISE |

Verdict rule applied: KEEP if >=70% exact, or >=90% within-1 for 0-3 scales.

### Three worst disagreements

1. **Bundle 17 `armandofox` 2013-04** — rater: category `other` (course autograder), audience `self`, collab `leading`; model: `developer_tool`, `developers`, `contributing`. The single item is a professor merging homework-grading support into `saasbook/rag` while directing a collaborator ("I don't know what you (Richard) were trying to do... please take a look", "I think we should either move... or make this repository private"). That is directing others on internal course tooling, not contributing a developer tool to an external audience. Model defaulted to its modal categories on thin evidence.
2. **Bundle 26 `aliscott` 2017-10** — rater: audience `customers`, intent `implicit`, commercial 1; model: `developers`, `none`, commercial 2. The bundle is customer-facing documentation and hosted-service infrastructure for AbarCloud ("our hosted services", official templates, load-balancer log docs for paying users). The model read a commercial PaaS operation as generic developer documentation — it scores surface commercial vocabulary but misses whose product it is. This is the single `commercial_language` disagreement and one of two missed venture-context cases (the other: bundle 29 `danielhanchen`, "we're still fixing things up... join our Discord").
3. **Bundle 19 `davidhu2000` 2022-10** — rater: intent `none`, collab `leading`, seriousness 2; model: `implicit`, `solo`, 1. Publishing `use-better-effect` to npm and maintaining `react-spinners` (responding to user bug reports, cutting 0.13.7) is routine OSS maintenance. Calling founding intent `implicit` here over-triggers on ordinary package publishing; calling a maintainer with an active user community `solo` shows the posture labels are not anchored (same pattern in bundles 02, 12, 21, 29; and `team_forming` appears for employer-org PRs in bundle 13).

### Summary

Scales behave well: all three 0-3 scales that both raters could actually score hit 100% within-1 with near-zero bias, and `commercial_language` is near-perfect exact. The weak fields are the three categoricals whose label boundaries are undefined at the margins: `building_what_category` needs tie-break rules (tool-vs-application, tool-vs-domain like `data_ai`/`security`/`hardware`), `audience_orientation` needs a rule for library-maintainer vs end-user-product vs coursework bundles, and `collaboration_posture` needs an explicit definition of `leading` (does answering your own repo's users count?). `domain_shift` cannot be validated with this sample design.
