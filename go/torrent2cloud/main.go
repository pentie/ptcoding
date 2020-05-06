package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/anacrolix/torrent/metainfo"
	"github.com/joho/godotenv"
)

func torrent2cloud(fn string) (string, error) {

	mi, err := metainfo.LoadFromFile(fn)
	if err != nil {
		return "", err
	}

	mi.Announce = ""
	mi.AnnounceList = metainfo.AnnounceList{}

	if ifo, err := mi.UnmarshalInfo(); err == nil {
		fmt.Println("[", ifo.Name, "]")
	}

	buff := &bytes.Buffer{}
	if err := mi.Write(buff); err != nil {
		return "", err
	}

	apiHost := os.Getenv("CLDTORRENT")
	magapi := apiHost + "/api/torrentfile"
	req, err := http.NewRequest("POST", magapi, buff)
	if err != nil {
		return "", err
	}

	req.Header.Set("content-type", "application/json;charset=utf-8")
	req.Header.Set("referer", apiHost)
	req.Header.Set("Cookie", strings.TrimPrefix(os.Getenv("CLDCOOKIE"), "cookie: "))
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func main() {

	cur, err := user.Current()
	if err != nil {
		log.Fatal(err)
	}
	_ = godotenv.Load(filepath.Join(cur.HomeDir, ".ptutils.config"))
	_ = godotenv.Load() // for .env

	tors, err := filepath.Glob(fmt.Sprintf("%s/*.torrent", os.Getenv("CLDTORRENTDIR")))
	if err != nil {
		return
	}

	for _, torf := range tors {
		fmt.Println("-->Load:", torf)
		retinfo, err := torrent2cloud(torf)
		if err != nil {
			fmt.Println(err)
		} else if strings.HasPrefix(retinfo, "OK") {
			if err := os.Remove(torf); err == nil {
				fmt.Println("-->Removed")
			}
		} else {
			fmt.Println("ret:", retinfo)
		}
		fmt.Println("===================================")
	}

	if runtime.GOOS == "windows" {
		fmt.Println("===================================")
		fmt.Println("\nPress 'Enter' to continue...")
		bufio.NewReader(os.Stdin).ReadBytes('\n')
	}
}
