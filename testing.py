me = "smart"
you = "dumb"
ans = input("are you smart or dumb? ")
while True:
    if ans == "dumb":
        print(f"Congrats! You are {me}!")
        break
    else:
        print("You're dumb")