package main

import (
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
)

func GetCateName(a string) (string, string) {
	re, err := regexp.Compile(`\[(.*)\] (.*)\.md`)
	if err != nil {
		panic(err)
	}
	// fmt.Println(re.FindString(a))
	return re.FindStringSubmatch(a)[1], a[:len(a)-3]
}

func TestGetCate() {
	if cat, name := GetCateName("[asdf] a.go"); cat != "asdf" && name != "a" {
		panic(cat + name)
	}
}

func tmpl(cat, name string) string {
	a := fmt.Sprintf(`---
title: "%s"
date: 2021-03-25
tags: ["%s"]
categories: ["%s"]
---

`, name, cat,cat)
	return a
}

func main() {
	// TestGetCate()

	entries, err := os.ReadDir("..")
	if err != nil {
		panic(err)
	}
	for _, v := range entries {
		if v.IsDir() {
			continue
		}
		bs, err := ioutil.ReadFile("../"+v.Name())
		if err != nil {
			panic(err)
		}
		fmt.Println(v.Name())
		cat, name := GetCateName(v.Name())
		str := tmpl(cat, name)
		f, err := os.OpenFile("../"+v.Name(), os.O_RDWR|os.O_CREATE, 0666)
		if err != nil {
			panic(err)
		}
		_, err = f.Write([]byte(str))
		// fmt.Println("n:", n)
		if err != nil {
			panic(err)
		}
		f.Write(bs)
		f.Close()
	}
}
