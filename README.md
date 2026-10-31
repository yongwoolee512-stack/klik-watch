# klik-watch — 영상 읽기 스킬 (유튜브·릴스·틱톡)

Claude Code에 영상 주소를 주면 **말소리를 글로 바꿔 내용을 읽는** 스킬입니다. 딸깍(Klik) 편집팀 제작.

- 유튜브·인스타 릴스·틱톡 공개 영상 지원
- 외부 서비스 없음: 음성 내려받기(yt-dlp)와 글로 바꾸기(faster-whisper) 모두 내 컴퓨터에서
- 처음 한 번 모델 파일(약 460MB)을 내려받습니다

## 설치

[딸깍](https://yongwoolee512-stack.github.io/klik-site/?open=klik-watch-video)에서 버튼 한 번, 또는 이 저장소의 `skills/watch-video` 폴더를 `~/.claude/skills/`에 복사.

준비물 (Python 3.10 이상):

```bash
python -m pip install --user --upgrade yt-dlp faster-whisper av numpy
```

## 쓰는 법

Claude Code 입력창에:

```
이 릴스에서 소개하는 도구가 뭐야? https://www.instagram.com/reel/XXXX/
```

```
이 유튜브 10줄로 요약해 줘 https://www.youtube.com/watch?v=XXXX
```

## 라이선스

MIT
